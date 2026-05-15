from __future__ import annotations

import time

import httpx

from app.agents.base import AgentContext, BaseAgent
from app.config import settings
from app.schemas.agents import AgentStatus, SentimentMLOutput


class SentimentMLAgent(BaseAgent[SentimentMLOutput]):
    name = "SentimentMLAgent"
    output_model = SentimentMLOutput

    async def run(self, ctx: AgentContext) -> SentimentMLOutput:
        t0 = time.perf_counter()
        base = settings.stock_prediction_api_url
        if not base:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("none", t0),
                confidence_note="Set STOCK_PREDICTION_API_URL to call your StockPrediction API.",
                raw_artifact={"hint": "http://127.0.0.1:8000/stock_analysis"},
            )
        url = base.rstrip("/") + "/stock_analysis"
        try:
            async with httpx.AsyncClient(timeout=ctx.timeout_s) as client:
                r = await client.post(url, json={"symbol": ctx.symbol})
                r.raise_for_status()
                data = r.json()
            pred = data.get("predcitions") or data.get("predictions") or {}
            sig = str(pred.get("trading_signal", "Hold"))
            sent = pred.get("sentiment_score")
            if sent is None:
                sent = data.get("sentiment_score")
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov("stock_prediction_api", t0),
                sentiment_score=float(sent) if sent is not None else None,
                forecast_signal=sig,
                confidence_note="From StockPrediction service; validate on your data before relying on signals.",
                raw_artifact={"trend": data.get("trend")},
            )
        except Exception as e:
            return SentimentMLOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("stock_prediction_api", t0),
                error_message=str(e),
                confidence_note="Upstream ML service unavailable.",
                raw_artifact={},
            )
