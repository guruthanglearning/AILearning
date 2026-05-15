from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

from app.agents.base import AgentContext
from app.agents.financials import FinancialsAgent
from app.agents.fundamentals import FundamentalsAgent
from app.agents.market_data import MarketDataAgent
from app.agents.options import OptionsAgent
from app.agents.risk_pro import RiskProWorkflowAgent
from app.agents.sentiment_ml import SentimentMLAgent
from app.agents.technicals import TechnicalsAgent
from app.config import settings
from app.db.models import AgentArtifact, AnalysisRun
from app.db.session import get_session
from app.decision_support import build_decision_aids
from app.providers.factory import build_provider
from app.schemas.agents import (
    AgentContribution,
    AgentStatus,
    AnalysisRunRequest,
    DataFreshness,
    InstrumentRecommendation,
    OptionsGuidance,
    SupervisorVerdict,
)

log = logging.getLogger(__name__)


class Supervisor:
    def __init__(self) -> None:
        self.market = MarketDataAgent()
        self.fundamentals = FundamentalsAgent()
        self.technicals = TechnicalsAgent()
        self.financials = FinancialsAgent()
        self.options = OptionsAgent()
        self.risk = RiskProWorkflowAgent()
        self.sentiment = SentimentMLAgent()

    async def run_analysis(self, req: AnalysisRunRequest) -> SupervisorVerdict:
        t0 = time.perf_counter()
        symbol = req.symbol.upper().strip()
        run_id = uuid.uuid4()
        provider = build_provider()

        # --- DB hook 1: open run record (best-effort; never blocks analysis) ---
        try:
            async for session in get_session():
                run_row = AnalysisRun(
                    id=run_id,
                    symbol=symbol,
                    status="running",
                    portfolio_value_usd=req.portfolio_value_usd,
                    max_risk_per_trade_pct=req.max_risk_per_trade_pct,
                )
                session.add(run_row)
                await session.commit()
        except Exception as exc:
            log.warning("DB: failed to create analysis_run row run_id=%s: %s", run_id, exc)

        ctx = AgentContext(symbol, timeout_s=settings.agent_timeout_seconds, provider=provider)

        m, f, tech, fin, opt, risk, sent = await asyncio.gather(
            self.market.safe_run(ctx),
            self.fundamentals.safe_run(ctx),
            self.technicals.safe_run(ctx),
            self.financials.safe_run(ctx),
            self.options.safe_run(ctx),
            self.risk.safe_run(ctx),
            self.sentiment.safe_run(ctx),
        )

        # --- DB hook 2: persist agent artifacts (best-effort) ---
        try:
            async for session in get_session():
                for agent_result in (m, f, tech, fin, opt, risk, sent):
                    artifact = AgentArtifact(
                        run_id=run_id,
                        agent_name=agent_result.agent_name,
                        status=agent_result.status.value,
                        latency_ms=agent_result.provenance.latency_ms
                        if agent_result.provenance
                        else None,
                        error_message=agent_result.error_message,
                        payload_json=agent_result.model_dump(mode="json"),
                    )
                    session.add(artifact)
                await session.commit()
        except Exception as exc:
            log.warning("DB: failed to persist agent artifacts run_id=%s: %s", run_id, exc)

        contributions: list[AgentContribution] = []
        for a in (m, f, tech, fin, opt, risk, sent):
            head = a.error_message or ("ok" if a.status == AgentStatus.complete else a.status.value)
            contributions.append(
                AgentContribution(agent_name=a.agent_name, status=a.status, headline=head, detail=None)
            )

        freshness = DataFreshness(
            quote_age_ms=int((time.perf_counter() - t0) * 1000),
            chain_age_ms=int((time.perf_counter() - t0) * 1000),
            fundamentals_as_of_note="See provider fundamentals snapshot timing",
        )

        decision_aids = await build_decision_aids(
            ctx.symbol,
            m.last_price,
            tech,
            opt,
            risk,
            req.portfolio_value_usd,
            req.max_risk_per_trade_pct,
            provider=provider,
            ml_forecast_signal=sent.forecast_signal,
        )

        verdict, options_guidance, note = self._merge(
            m, tech, opt, risk, decision_aids.stock_vs_options_score
        )

        result = SupervisorVerdict(
            instrument_recommendation=verdict,
            confidence_note=note,
            options=options_guidance,
            agent_contributions=contributions,
            data_freshness=freshness,
            decision_aids=decision_aids,
        )

        # --- DB hook 3: finalise run record (best-effort) ---
        try:
            async for session in get_session():
                row = await session.get(AnalysisRun, run_id)
                if row is not None:
                    row.status = "complete"
                    row.finished_at = datetime.now(tz=timezone.utc)
                    row.instrument_recommendation = verdict.value
                    row.confidence_note = note
                    row.verdict_json = result.model_dump(mode="json")
                    await session.commit()
        except Exception as exc:
            log.warning("DB: failed to finalise analysis_run run_id=%s: %s", run_id, exc)

        return result

    def _merge(self, m, tech, opt, risk, stock_vs_opt_score: float):
        if m.status == AgentStatus.failed or m.last_price is None:
            return (
                InstrumentRecommendation.insufficient_data,
                None,
                "Market data agent failed; cannot recommend instruments.",
            )

        # Earnings: push toward defined-risk options or no trade
        if risk.has_upcoming_earnings and (tech.trend_hint or "mixed") == "mixed":
            og = OptionsGuidance(
                strategy_family="debit_vertical_or_long_put_call",
                rationale_codes=["earnings_soon", "direction_unclear"],
                strike_guidance="Use your broker chain: pick ~30-45 DTE unless vol event dictates shorter.",
                max_loss_scenario="Premium / net debit is max loss for long premium; size small vs portfolio.",
                profit_targets_scenario=["Scale at +25-40% of max profit for debit spreads", "Trail stock stop if trading shares"],
            )
            return (
                InstrumentRecommendation.options,
                og,
                "Earnings window with mixed technicals — prefer defined-risk options or avoid.",
            )

        options_ok = opt.status != AgentStatus.failed and opt.atm_iv is not None
        iv_rich = opt.atm_iv and opt.atm_iv > 0.35

        if not options_ok:
            og = None
            if stock_vs_opt_score < -0.2:
                note = "Options data degraded — stock-only path unless you verify chain at broker."
            else:
                note = "Options data missing or weak; stock is the default actionable lane."
            return InstrumentRecommendation.stock, og, note

        # IV-rich + not immediate earnings -> credit-style options umbrella
        if iv_rich and not risk.has_upcoming_earnings and (tech.trend_hint or "") != "bearish":
            og = OptionsGuidance(
                strategy_family="premium_selling_or_covered_call",
                rationale_codes=["iv_elevated", "no_imminent_earnings_flag"],
                strike_guidance="OTM calls for covered calls or OTM credit spreads vs support/resistance you define.",
                max_loss_scenario="For credit spreads: width minus credit; for covered stock: stock minus call premium.",
                profit_targets_scenario=["Take 50% of max credit early", "Roll only with a written rule"],
            )
            return (
                InstrumentRecommendation.options,
                og,
                "IV looks elevated vs simple heuristics — options structures may be efficient vs naked long calls.",
            )

        if (stock_vs_opt_score > 0.25 or (tech.trend_hint or "") in ("bullish", "bearish")) and not iv_rich:
            og = OptionsGuidance(
                strategy_family="long_stock_or_long_diagonal",
                rationale_codes=["directional_clarity", "iv_not_extreme"],
                strike_guidance="If using options for leverage, prefer debit spreads over naked long if IV is mid/high.",
                max_loss_scenario="Stock: stop-based; long option: premium; spread: net debit.",
                profit_targets_scenario=["Match horizon to thesis weeks/months", "Pre-define exit on thesis break"],
            )
            return (
                InstrumentRecommendation.stock,
                og,
                "Directional context favors owning delta via stock or long-biased simple structures.",
            )

        og = OptionsGuidance(
            strategy_family="debit_spread_or_stock",
            rationale_codes=["balanced_regime"],
            strike_guidance="Compare breakevens of stock vs debit vertical at same directional bias.",
            max_loss_scenario="Define max loss before entry for either lane.",
            profit_targets_scenario=["Use decision_aids.instrument_plays to pick structure"],
        )
        return (
            InstrumentRecommendation.options if stock_vs_opt_score < 0 else InstrumentRecommendation.stock,
            og,
            "Balanced regime — see decision_aids checklist and plays.",
        )
