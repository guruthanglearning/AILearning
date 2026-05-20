"""FinBERT + Finnhub News sentiment agent — self-contained, no external service required."""
from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta

import httpx
import structlog

from app.agents.base import AgentContext, BaseAgent
from app.config import settings
from app.schemas.agents import AgentStatus, SentimentMLOutput

log = structlog.get_logger(__name__)

_FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/company-news"

# ── FinBERT availability check (import once at module load) ───────────────────
try:
    import transformers as _  # noqa: F401
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False

# ── Lazy singleton pipeline ───────────────────────────────────────────────────
_pipeline_lock = asyncio.Lock()
_finbert = None


def _load_finbert_sync():
    from transformers import pipeline  # noqa: PLC0415
    return pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        top_k=None,
        truncation=True,
        max_length=512,
    )


async def _get_pipeline():
    global _finbert
    if _finbert is None:
        async with _pipeline_lock:
            if _finbert is None:
                loop = asyncio.get_running_loop()
                _finbert = await loop.run_in_executor(None, _load_finbert_sync)
    return _finbert


# ── Finnhub news fetch (async) ────────────────────────────────────────────────

async def _fetch_headlines(symbol: str, api_key: str, timeout: float) -> list[str]:
    """Fetch last 7 days of company news headlines from Finnhub."""
    to_date = datetime.now(UTC)
    from_date = to_date - timedelta(days=7)
    params = {
        "symbol": symbol,
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d"),
        "token": api_key,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(_FINNHUB_NEWS_URL, params=params)
        resp.raise_for_status()
        articles = resp.json()
    return [a["headline"] for a in articles if a.get("headline")]


# ── FinBERT scoring (synchronous, run in thread pool) ─────────────────────────

def _score_headlines(pipe, headlines: list[str]) -> tuple[float, list[str]]:
    """Score headlines with FinBERT; return (aggregate_score [-1..+1], top_3_headlines)."""
    scored: list[tuple[float, str]] = []
    for title in headlines[:15]:  # cap to keep latency manageable
        results = pipe(title)
        # transformers may return [[{...}]] or [{...}] depending on version
        if results and isinstance(results[0], list):
            results = results[0]
        label_map = {r["label"]: r["score"] for r in results}
        polarity = label_map.get("positive", 0.0) - label_map.get("negative", 0.0)
        scored.append((polarity, title))

    if not scored:
        return 0.0, []

    agg = sum(p for p, _ in scored) / len(scored)
    top = [t for _, t in sorted(scored, key=lambda x: abs(x[0]), reverse=True)[:3]]
    return round(agg, 4), top


def _to_signal(score: float) -> str:
    if score > 0.15:
        return "Bullish"
    if score < -0.15:
        return "Bearish"
    return "Neutral"


# ── Agent ─────────────────────────────────────────────────────────────────────

class SentimentMLAgent(BaseAgent[SentimentMLOutput]):
    name = "SentimentMLAgent"
    output_model = SentimentMLOutput

    async def run(self, ctx: AgentContext) -> SentimentMLOutput:
        t0 = time.perf_counter()

        if not settings.finnhub_api_key:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("none", t0),
                confidence_note="Set FINNHUB_API_KEY in .env to enable FinBERT sentiment analysis.",
                raw_artifact={},
            )

        if not _HF_AVAILABLE:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("none", t0),
                confidence_note="Install 'transformers' and 'torch' to enable FinBERT sentiment.",
                raw_artifact={},
            )

        try:
            headlines = await _fetch_headlines(
                ctx.symbol, settings.finnhub_api_key, ctx.timeout_s
            )
        except Exception as exc:
            log.warning("finnhub_fetch_failed", symbol=ctx.symbol, error=str(exc))
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("finnhub", t0),
                error_message=str(exc),
                confidence_note="Finnhub news fetch failed.",
                raw_artifact={},
            )

        if not headlines:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("finnhub", t0),
                confidence_note=f"No recent news found for {ctx.symbol}.",
                raw_artifact={"headline_count": 0},
            )

        try:
            loop = asyncio.get_running_loop()
            pipe = await _get_pipeline()
            score, top_headlines = await loop.run_in_executor(
                None, _score_headlines, pipe, headlines
            )
        except Exception as exc:
            log.warning("finbert_inference_failed", symbol=ctx.symbol, error=str(exc))
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("finbert", t0),
                error_message=str(exc),
                confidence_note="FinBERT inference failed.",
                raw_artifact={},
            )

        signal = _to_signal(score)
        return SentimentMLOutput(
            agent_name=self.name,
            status=AgentStatus.complete,
            provenance=self._prov("finbert+finnhub", t0),
            sentiment_score=score,
            forecast_signal=signal,
            top_headlines=top_headlines,
            confidence_note=(
                f"FinBERT scored {len(headlines)} Finnhub headlines — {signal} ({score:+.3f})."
            ),
            raw_artifact={"headline_count": len(headlines)},
        )
