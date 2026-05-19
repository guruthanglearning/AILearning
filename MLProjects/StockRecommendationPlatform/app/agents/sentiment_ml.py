"""FinBERT + NewsAPI sentiment agent — self-contained, no external service required."""
from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta

import structlog

from app.agents.base import AgentContext, BaseAgent
from app.config import settings
from app.schemas.agents import AgentStatus, SentimentMLOutput

log = structlog.get_logger(__name__)

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


# ── NewsAPI fetch (synchronous, run in thread pool) ───────────────────────────

def _fetch_articles_sync(symbol: str, api_key: str) -> list[str]:
    from newsapi import NewsApiClient  # noqa: PLC0415
    client = NewsApiClient(api_key=api_key)
    from_date = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")
    resp = client.get_everything(
        q=f"{symbol} stock",
        language="en",
        sort_by="publishedAt",
        page_size=20,
        from_param=from_date,
    )
    return [a["title"] for a in resp.get("articles", []) if a.get("title")]


# ── FinBERT scoring (synchronous, run in thread pool) ─────────────────────────

def _score_headlines(pipe, headlines: list[str]) -> tuple[float, list[str]]:
    """Score headlines with FinBERT; return (aggregate_score [-1..+1], top_3_headlines)."""
    scored: list[tuple[float, str]] = []
    for title in headlines[:15]:  # cap to keep latency manageable
        results = pipe(title)
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

        if not settings.news_api_key:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("none", t0),
                confidence_note="Set NEWS_API_KEY in .env to enable FinBERT sentiment analysis.",
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

        loop = asyncio.get_running_loop()

        try:
            headlines = await loop.run_in_executor(
                None, _fetch_articles_sync, ctx.symbol, settings.news_api_key
            )
        except Exception as exc:
            log.warning("newsapi_fetch_failed", symbol=ctx.symbol, error=str(exc))
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("newsapi", t0),
                error_message=str(exc),
                confidence_note="NewsAPI fetch failed.",
                raw_artifact={},
            )

        if not headlines:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("newsapi", t0),
                confidence_note=f"No recent news found for {ctx.symbol}.",
                raw_artifact={"headline_count": 0},
            )

        try:
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
            provenance=self._prov("finbert+newsapi", t0),
            sentiment_score=score,
            forecast_signal=signal,
            top_headlines=top_headlines,
            confidence_note=(
                f"FinBERT scored {len(headlines)} headlines — {signal} ({score:+.3f})."
            ),
            raw_artifact={"headline_count": len(headlines)},
        )
