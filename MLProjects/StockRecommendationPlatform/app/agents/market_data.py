from __future__ import annotations

import time

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, MarketDataOutput


class MarketDataAgent(BaseAgent[MarketDataOutput]):
    name = "MarketDataAgent"

    async def run(self, ctx: AgentContext) -> MarketDataOutput:
        t0 = time.perf_counter()
        try:
            data = await ctx.provider.get_quote(ctx.symbol)
            if data["last_price"] is None:
                return self._fail(MarketDataOutput, t0, data["source"], "No price data")
            return MarketDataOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov(data["source"], t0),
                last_price=data["last_price"],
                previous_close=data["previous_close"],
                day_change_pct=data["day_change_pct"],
                volume=data["volume"],
                market_state=None,
                raw_artifact={"symbol": ctx.symbol},
            )
        except Exception as e:
            return self._fail(MarketDataOutput, t0, "provider", str(e))
