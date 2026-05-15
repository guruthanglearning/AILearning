from __future__ import annotations

import time

import numpy as np
import pandas as pd

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, TechnicalsOutput


def _rsi(series: pd.Series, period: int = 14) -> float | None:
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    v = rsi.iloc[-1]
    return float(v) if pd.notna(v) else None


class TechnicalsAgent(BaseAgent[TechnicalsOutput]):
    name = "TechnicalsAgent"

    async def run(self, ctx: AgentContext) -> TechnicalsOutput:
        t0 = time.perf_counter()
        try:
            hist = await ctx.provider.get_price_history(ctx.symbol, "6mo")
            if hist.empty or len(hist) < 50:
                return TechnicalsOutput(
                    agent_name=self.name,
                    status=AgentStatus.degraded,
                    provenance=self._prov("provider", t0),
                    error_message="Insufficient history",
                    raw_artifact={},
                )
            close = hist["Close"]
            sma20 = float(close.rolling(20).mean().iloc[-1])
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = _rsi(close, 14)
            if sma20 > sma50 and (rsi or 50) > 50:
                trend = "bullish"
            elif sma20 < sma50 and (rsi or 50) < 50:
                trend = "bearish"
            else:
                trend = "mixed"
            return TechnicalsOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov("provider", t0),
                sma_20=sma20,
                sma_50=sma50,
                rsi_14=rsi,
                trend_hint=trend,
                raw_artifact={"bars": len(hist)},
            )
        except Exception as e:
            return self._fail(TechnicalsOutput, t0, "provider", str(e))
