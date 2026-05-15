from __future__ import annotations

import time

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, FinancialsOutput


class FinancialsAgent(BaseAgent[FinancialsOutput]):
    name = "FinancialsAgent"

    async def run(self, ctx: AgentContext) -> FinancialsOutput:
        t0 = time.perf_counter()
        try:
            # Price history used as a proxy for data availability; full financials
            # require Polygon financials endpoint (future phase) or SEC EDGAR.
            hist = await ctx.provider.get_price_history(ctx.symbol, "1y")
            source = "provider"
            rows = len(hist) if not hist.empty else 0
            summary = (
                f"Annual price history bars available: {rows}. "
                "Review full financial statements via SEC EDGAR for decisions."
            )
            return FinancialsOutput(
                agent_name=self.name,
                status=AgentStatus.complete if rows else AgentStatus.degraded,
                provenance=self._prov(source, t0),
                summary=summary,
                filing_url_hint=(
                    f"https://www.sec.gov/cgi-bin/browse-edgar?"
                    f"action=getcompany&CIK=&type=10-Q&dateb=&owner=exclude"
                    f"&count=40&search_text={ctx.symbol}"
                ),
                raw_artifact={"annual_price_bars": int(rows)},
            )
        except Exception as e:
            return FinancialsOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("provider", t0),
                error_message=str(e),
                summary="Financials unavailable from data feed.",
                raw_artifact={},
            )
