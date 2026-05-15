from __future__ import annotations

import time

import pandas as pd

from app.agents.base import AgentContext, BaseAgent
from app.schemas.agents import AgentStatus, RiskProOutput


class RiskProWorkflowAgent(BaseAgent[RiskProOutput]):
    name = "RiskProWorkflowAgent"
    output_model = RiskProOutput

    async def run(self, ctx: AgentContext) -> RiskProOutput:
        t0 = time.perf_counter()
        checklist: list[dict] = []
        try:
            data = await ctx.provider.get_fundamentals(ctx.symbol)
            source = data.get("source", "provider")

            # Earnings window — providers surface this when available
            days = self._days_to_earnings(data.get("earnings_dates"))
            has_earnings = days is not None and days <= 21
            checklist.append(
                {
                    "id": "earnings_window",
                    "label": "Earnings within 3 weeks",
                    "pass": not has_earnings,
                    "detail": f"Next earnings ~{days}d" if days is not None else "Unknown",
                }
            )

            avg_vol = data.get("avg_volume")
            checklist.append(
                {
                    "id": "liquidity",
                    "label": "Average volume acceptable (>500k ideal)",
                    "pass": (avg_vol or 0) >= 200_000,
                    "detail": f"Avg volume proxy: {avg_vol}",
                }
            )

            return RiskProOutput(
                agent_name=self.name,
                status=AgentStatus.complete,
                provenance=self._prov(source, t0),
                earnings_days_away=days,
                has_upcoming_earnings=bool(has_earnings),
                checklist=checklist,
                raw_artifact={},
            )
        except Exception as e:
            return RiskProOutput(
                agent_name=self.name,
                status=AgentStatus.degraded,
                provenance=self._prov("provider", t0),
                error_message=str(e),
                checklist=checklist,
                raw_artifact={},
            )

    @staticmethod
    def _days_to_earnings(earnings_dates) -> int | None:
        if earnings_dates is None:
            return None
        try:
            if isinstance(earnings_dates, list):
                today = pd.Timestamp.today().normalize()
                future = [
                    pd.Timestamp(d).normalize()
                    for d in earnings_dates
                    if pd.Timestamp(d).normalize() >= today
                ]
                if not future:
                    return None
                nxt = min(future)
                return max(0, int((nxt - today).days))
        except Exception:
            pass
        return None
