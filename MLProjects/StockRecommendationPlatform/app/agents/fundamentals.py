from __future__ import annotations

import time

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, FundamentalsOutput


class FundamentalsAgent(BaseAgent[FundamentalsOutput]):
    name = "FundamentalsAgent"

    async def run(self, ctx: AgentContext) -> FundamentalsOutput:
        t0 = time.perf_counter()
        try:
            data = await ctx.provider.get_fundamentals(ctx.symbol)
            return FundamentalsOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov(data["source"], t0),
                company_name=data["company_name"],
                sector=data["sector"],
                market_cap=data["market_cap"],
                pe_ratio=data["pe_ratio"],
                forward_pe=data["forward_pe"],
                revenue_growth=data["revenue_growth"],
                raw_artifact={"source": data["source"]},
            )
        except Exception as e:
            return FundamentalsOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("provider", t0),
                error_message=str(e),
                raw_artifact={},
            )
