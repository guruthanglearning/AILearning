from __future__ import annotations

import asyncio
import time
import traceback
import uuid
from datetime import UTC, datetime

import structlog

import app.error_log as error_log
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
from app.observability import agent_latency_histogram, get_correlation_id, get_tracer
from app.providers.factory import build_provider
from app.schemas.agents import (
    AgentContribution,
    AgentResultBase,
    AgentStatus,
    AnalysisRunRequest,
    DataFreshness,
    DecisionAids,
    FinancialsOutput,
    FundamentalsOutput,
    FundamentalsSnapshot,
    InstrumentRecommendation,
    MarketDataOutput,
    OptionLegType,
    OptionsGuidance,
    OptionsOutput,
    RiskProOutput,
    SentimentMLOutput,
    SupervisorVerdict,
    TechnicalsOutput,
)
from app.services.claude_service import get_claude_verdict

log = structlog.get_logger(__name__)
_tracer = get_tracer("app.supervisor")


def _fmt_cap(cap: float | None) -> str:
    if cap is None:
        return "n/a"
    if cap >= 1e12:
        return f"${cap/1e12:.2f}T"
    if cap >= 1e9:
        return f"${cap/1e9:.1f}B"
    return f"${cap/1e6:.0f}M"


_FAMILY_TO_TEMPLATE: dict[str, str] = {
    "long_stock_or_long_diagonal":    "bull_call_spread",
    "debit_vertical_or_long_put_call": "bull_call_spread",
    "debit_spread_or_stock":           "bull_call_spread",
    "premium_selling_or_covered_call": "short_put_spread",
}


def _validate_strike_guidance(
    og: OptionsGuidance | None,
    decision_aids: DecisionAids,
) -> OptionsGuidance | None:
    """Enrich OptionsGuidance with real strikes from the computed chain rows.

    Finds the OptionsMetricRow whose template_id matches the strategy family,
    and when it has quality=='full' (real chain data), stamps chain_validated=True
    and populates chain_verified_strikes with a human-readable leg description.
    The original strike_guidance text is preserved unchanged.
    """
    if og is None:
        return None
    template_id = _FAMILY_TO_TEMPLATE.get(og.strategy_family or "", "bull_call_spread")
    row = next(
        (r for r in decision_aids.options_metrics_table if r.template_id == template_id),
        None,
    )
    if row is None or row.row_data_quality != "full" or not row.legs:
        return og

    leg_parts: list[str] = []
    for leg in row.legs:
        action = "Buy" if leg.leg_type == OptionLegType.long else "Sell"
        leg_parts.append(f"{action} ${leg.strike:.0f} {leg.right}")
    expiry_note = f" exp {row.expiration}" if row.expiration else ""
    verified_str = " / ".join(leg_parts) + expiry_note

    return og.model_copy(update={
        "chain_validated": True,
        "chain_verified_strikes": verified_str,
        "validated_legs": list(row.legs),
    })


def _agent_summary(a: AgentResultBase) -> tuple[str, str | None]:
    """Return (headline, detail) for an agent result — called only when status=complete."""
    if isinstance(a, MarketDataOutput):
        price = f"${a.last_price:.2f}" if a.last_price is not None else "n/a"
        chg = f"{a.day_change_pct:+.2f}%" if a.day_change_pct is not None else ""
        vol = f"Vol {a.volume/1e6:.1f}M" if a.volume else ""
        parts = [p for p in [price, chg, vol] if p]
        return ", ".join(parts), None

    if isinstance(a, FundamentalsOutput):
        name = a.company_name or ""
        sector = a.sector or "Unknown sector"
        cap = _fmt_cap(a.market_cap)
        headline = f"{name} — {sector}, Cap {cap}"
        details = []
        if a.pe_ratio is not None:
            details.append(f"P/E {a.pe_ratio:.1f}")
        if a.forward_pe is not None:
            details.append(f"Fwd P/E {a.forward_pe:.1f}")
        if a.revenue_growth is not None:
            details.append(f"Rev growth {a.revenue_growth*100:.1f}%")
        return headline, " · ".join(details) or None

    if isinstance(a, TechnicalsOutput):
        trend = (a.trend_hint or "neutral").capitalize()
        rsi = f"RSI14 {a.rsi_14:.1f}" if a.rsi_14 is not None else ""
        headline = f"Trend: {trend}" + (f", {rsi}" if rsi else "")
        detail_parts = []
        if a.sma_20 and a.sma_50:
            detail_parts.append(f"SMA20 ${a.sma_20:.2f} / SMA50 ${a.sma_50:.2f}")
        if a.ema_20:
            detail_parts.append(f"EMA20 ${a.ema_20:.2f}")
        if a.atr_pct_14:
            detail_parts.append(f"ATR14 {a.atr_pct_14:.2f}%")
        return headline, " · ".join(detail_parts) or None

    if isinstance(a, FinancialsOutput):
        if a.summary:
            lines = a.summary.splitlines()
            return lines[0], "\n".join(lines[1:]).strip() or None
        return "Financials fetched", None

    if isinstance(a, OptionsOutput):
        iv = f"ATM IV {a.atm_iv*100:.1f}%" if a.atm_iv is not None else "IV n/a"
        move = f"±{a.implied_move_1d_pct:.2f}% implied" if a.implied_move_1d_pct else ""
        liq = a.chain_liquidity_hint or ""
        parts = [p for p in [iv, move, liq] if p]
        expiry = f"Nearest expiry {a.nearest_expiry}" if a.nearest_expiry else None
        return ", ".join(parts), expiry

    if isinstance(a, RiskProOutput):
        if a.has_upcoming_earnings and a.earnings_days_away is not None:
            headline = f"Earnings in {a.earnings_days_away}d — elevated event risk"
        elif a.has_upcoming_earnings:
            headline = "Upcoming earnings detected"
        else:
            headline = "No imminent earnings"
        n_checks = len(a.checklist)
        passed = sum(1 for c in a.checklist if c.get("state") == "pass")
        detail = f"{passed}/{n_checks} risk checks passed" if n_checks else None
        return headline, detail

    if isinstance(a, SentimentMLOutput):
        signal = a.forecast_signal or "Neutral"
        score = f"{a.sentiment_score:+.3f}" if a.sentiment_score is not None else ""
        headline = f"{signal} ({score})" if score else signal
        detail = a.top_headlines[0] if a.top_headlines else a.confidence_note
        return headline, detail

    return "complete", None


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

        with _tracer.start_as_current_span(
            "supervisor.run_analysis",
            attributes={"symbol": symbol, "correlation_id": get_correlation_id()},
        ):
            # --- DB hook 1: open run record (best-effort; never blocks analysis) ---
            try:
                async for session in get_session():
                    run_row = AnalysisRun(
                        id=run_id,
                        symbol=symbol,
                        status="running",
                        portfolio_value_usd=req.portfolio_value_usd,
                        max_risk_per_trade_pct=req.max_risk_per_trade_pct,
                        batch_job_id=req.batch_job_id,
                        last_price=None,
                    )
                    session.add(run_row)
                    await session.commit()
            except Exception as exc:
                log.warning("db_open_run_failed", run_id=str(run_id), error=str(exc))

            ctx = AgentContext(symbol, timeout_s=settings.agent_timeout_seconds, provider=provider)

            with _tracer.start_as_current_span("supervisor.gather_agents"):
                m, f, tech, fin, opt, risk, sent = await asyncio.gather(
                    self.market.safe_run(ctx),
                    self.fundamentals.safe_run(ctx),
                    self.technicals.safe_run(ctx),
                    self.financials.safe_run(ctx),
                    self.options.safe_run(ctx),
                    self.risk.safe_run(ctx),
                    self.sentiment.safe_run(ctx),
                )

            # Emit per-agent latency histogram
            for agent_result in (m, f, tech, fin, opt, risk, sent):
                if agent_result.provenance and agent_result.provenance.latency_ms is not None:
                    agent_latency_histogram.labels(
                        agent_name=agent_result.agent_name,
                        status=agent_result.status.value,
                    ).observe(agent_result.provenance.latency_ms / 1000.0)

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
                log.warning("db_persist_artifacts_failed", run_id=str(run_id), error=str(exc))

        contributions: list[AgentContribution] = []
        for a in (m, f, tech, fin, opt, risk, sent):
            if a.status == AgentStatus.complete:
                head, det = _agent_summary(a)
            else:
                head = a.error_message or a.status.value
                det = None
                if a.error_message:
                    error_log.record(
                        symbol=req.symbol, agent=a.agent_name,
                        status=a.status.value, message=a.error_message,
                    )
            contributions.append(
                AgentContribution(agent_name=a.agent_name, status=a.status, headline=head, detail=det)
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

        # --- Insufficient data early-exit (before Claude call) ---
        if m.status == AgentStatus.failed or m.last_price is None:
            verdict = InstrumentRecommendation.insufficient_data
            options_guidance = None
            note = "Market data agent failed; cannot produce an AI-powered recommendation."
        else:
            # --- Claude LLM verdict (no fallback — failure surfaces to the caller) ---
            try:
                claude = await get_claude_verdict(symbol, m, f, tech, opt, risk, sent, decision_aids, model=req.claude_model)
            except Exception as exc:
                error_log.record(
                    symbol=symbol,
                    agent="ClaudeDecisionEngine",
                    status="claude_failed",
                    message=str(exc),
                    detail=traceback.format_exc(),
                )
                log.error("claude_verdict_failed", symbol=symbol, error=str(exc))
                raise

            verdict = claude.instrument_recommendation
            options_guidance = claude.options_guidance
            note = claude.confidence_note
            decision_aids.summary_headline = claude.summary_headline
            if claude.user_answers:
                decision_aids.user_answers = claude.user_answers
            log.info("claude_verdict_applied", symbol=symbol, recommendation=verdict.value)

        options_guidance = _validate_strike_guidance(options_guidance, decision_aids)
        if options_guidance is not None:
            options_guidance = options_guidance.model_copy(update={"chain_source": opt.provenance.source})

        result = SupervisorVerdict(
            instrument_recommendation=verdict,
            confidence_note=note,
            options=options_guidance,
            agent_contributions=contributions,
            data_freshness=freshness,
            decision_aids=decision_aids,
            technicals=tech if tech.status == AgentStatus.complete else None,
            fundamentals=self._fundamentals_snapshot(f),
            sentiment_headlines=sent.top_headlines if sent.status == AgentStatus.complete else [],
            sentiment_forecast=sent.forecast_signal if sent.status == AgentStatus.complete else None,
            sentiment_score=sent.sentiment_score if sent.status == AgentStatus.complete else None,
            earnings_days_away=risk.earnings_days_away,
            has_upcoming_earnings=risk.has_upcoming_earnings,
        )

        # --- DB hook 3: finalise run record (best-effort) ---
        try:
            async for session in get_session():
                row = await session.get(AnalysisRun, run_id)
                if row is not None:
                    row.status = "complete"
                    row.finished_at = datetime.now(tz=UTC)
                    row.instrument_recommendation = verdict.value
                    row.confidence_note = note
                    row.last_price = m.last_price
                    row.verdict_json = result.model_dump(mode="json")
                    await session.commit()
        except Exception as exc:
            log.warning("db_finalise_run_failed", run_id=str(run_id), error=str(exc))

        return result

    async def stream_analysis(self, req: AnalysisRunRequest):
        """Async generator. Yields one dict per agent as it completes, then verdict + done."""
        t0 = time.perf_counter()
        symbol = req.symbol.upper().strip()
        run_id = uuid.uuid4()
        provider = build_provider()

        try:
            async for session in get_session():
                run_row = AnalysisRun(
                    id=run_id,
                    symbol=symbol,
                    status="running",
                    portfolio_value_usd=req.portfolio_value_usd,
                    max_risk_per_trade_pct=req.max_risk_per_trade_pct,
                    batch_job_id=getattr(req, "batch_job_id", None),
                    last_price=None,
                )
                session.add(run_row)
                await session.commit()
        except Exception as exc:
            log.warning("db_open_run_failed", run_id=str(run_id), error=str(exc))

        ctx = AgentContext(symbol, timeout_s=settings.agent_timeout_seconds, provider=provider)

        pending_tasks: set[asyncio.Task] = {
            asyncio.create_task(agent.safe_run(ctx))
            for agent in (
                self.market, self.fundamentals, self.technicals,
                self.financials, self.options, self.risk, self.sentiment,
            )
        }
        results_by_name: dict[str, AgentResultBase] = {}

        while pending_tasks:
            done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                a: AgentResultBase = task.result()
                results_by_name[a.agent_name] = a
                if a.status == AgentStatus.complete:
                    head, det = _agent_summary(a)
                else:
                    head = a.error_message or a.status.value
                    det = None
                    if a.error_message:
                        error_log.record(
                            symbol=req.symbol, agent=a.agent_name,
                            status=a.status.value, message=a.error_message,
                        )
                yield {"type": "agent_done", "agent": a.agent_name, "status": a.status.value, "headline": head, "detail": det}

        for a in results_by_name.values():
            if a.provenance and a.provenance.latency_ms is not None:
                agent_latency_histogram.labels(agent_name=a.agent_name, status=a.status.value).observe(
                    a.provenance.latency_ms / 1000.0
                )

        try:
            async for session in get_session():
                for a in results_by_name.values():
                    session.add(AgentArtifact(
                        run_id=run_id,
                        agent_name=a.agent_name,
                        status=a.status.value,
                        latency_ms=a.provenance.latency_ms if a.provenance else None,
                        error_message=a.error_message,
                        payload_json=a.model_dump(mode="json"),
                    ))
                await session.commit()
        except Exception as exc:
            log.warning("db_persist_artifacts_failed", run_id=str(run_id), error=str(exc))

        _ORDER = ["MarketDataAgent", "FundamentalsAgent", "TechnicalsAgent",
                  "FinancialsAgent", "OptionsAgent", "RiskProWorkflowAgent", "SentimentMLAgent"]
        contributions: list[AgentContribution] = []
        for name in _ORDER:
            a = results_by_name.get(name)
            if a is None:
                continue
            if a.status == AgentStatus.complete:
                head, det = _agent_summary(a)
            else:
                head = a.error_message or a.status.value
                det = None
            contributions.append(AgentContribution(agent_name=a.agent_name, status=a.status, headline=head, detail=det))

        m    = results_by_name["MarketDataAgent"]
        f    = results_by_name["FundamentalsAgent"]
        tech = results_by_name["TechnicalsAgent"]
        opt  = results_by_name["OptionsAgent"]
        risk = results_by_name["RiskProWorkflowAgent"]
        sent = results_by_name["SentimentMLAgent"]

        freshness = DataFreshness(
            quote_age_ms=int((time.perf_counter() - t0) * 1000),
            chain_age_ms=int((time.perf_counter() - t0) * 1000),
            fundamentals_as_of_note="See provider fundamentals snapshot timing",
        )

        decision_aids = await build_decision_aids(
            ctx.symbol,
            m.last_price,  # type: ignore[attr-defined]
            tech, opt, risk,
            req.portfolio_value_usd,
            req.max_risk_per_trade_pct,
            provider=provider,
            ml_forecast_signal=sent.forecast_signal,  # type: ignore[attr-defined]
        )

        # --- Insufficient data early-exit (before Claude call) ---
        if m.status == AgentStatus.failed or m.last_price is None:  # type: ignore[attr-defined]
            verdict = InstrumentRecommendation.insufficient_data
            options_guidance = None
            note = "Market data agent failed; cannot produce an AI-powered recommendation."
        else:
            # --- Claude LLM verdict (no fallback — failure surfaces to the caller) ---
            try:
                claude = await get_claude_verdict(symbol, m, f, tech, opt, risk, sent, decision_aids, model=req.claude_model)
            except Exception as exc:
                error_log.record(
                    symbol=symbol,
                    agent="ClaudeDecisionEngine",
                    status="claude_failed",
                    message=str(exc),
                    detail=traceback.format_exc(),
                )
                log.error("claude_verdict_failed", symbol=symbol, error=str(exc))
                raise

            verdict = claude.instrument_recommendation
            options_guidance = claude.options_guidance
            note = claude.confidence_note
            decision_aids.summary_headline = claude.summary_headline
            if claude.user_answers:
                decision_aids.user_answers = claude.user_answers
            log.info("claude_verdict_applied", symbol=symbol, recommendation=verdict.value)

        options_guidance = _validate_strike_guidance(options_guidance, decision_aids)
        if options_guidance is not None:
            options_guidance = options_guidance.model_copy(update={"chain_source": opt.provenance.source})

        result = SupervisorVerdict(
            instrument_recommendation=verdict,
            confidence_note=note,
            options=options_guidance,
            agent_contributions=contributions,
            data_freshness=freshness,
            decision_aids=decision_aids,
            technicals=tech if tech.status == AgentStatus.complete else None,
            fundamentals=self._fundamentals_snapshot(f),
            sentiment_headlines=sent.top_headlines if sent.status == AgentStatus.complete else [],
            sentiment_forecast=sent.forecast_signal if sent.status == AgentStatus.complete else None,
            sentiment_score=sent.sentiment_score if sent.status == AgentStatus.complete else None,
            earnings_days_away=risk.earnings_days_away,
            has_upcoming_earnings=risk.has_upcoming_earnings,
        )

        try:
            async for session in get_session():
                row = await session.get(AnalysisRun, run_id)
                if row is not None:
                    row.status = "complete"
                    row.finished_at = datetime.now(tz=UTC)
                    row.instrument_recommendation = verdict.value
                    row.confidence_note = note
                    row.last_price = m.last_price  # type: ignore[attr-defined]
                    row.verdict_json = result.model_dump(mode="json")
                    await session.commit()
        except Exception as exc:
            log.warning("db_finalise_run_failed", run_id=str(run_id), error=str(exc))

        yield {"type": "verdict", "data": result.model_dump(mode="json")}
        yield {"type": "done"}

    @staticmethod
    def _fundamentals_snapshot(f: FundamentalsOutput) -> FundamentalsSnapshot | None:
        if f.status != AgentStatus.complete:
            return None
        return FundamentalsSnapshot(
            company_name=f.company_name,
            sector=f.sector,
            market_cap=f.market_cap,
            pe_ratio=f.pe_ratio,
            forward_pe=f.forward_pe,
            revenue_growth=f.revenue_growth,
        )

    def _merge(self, m, tech, opt, risk, stock_vs_opt_score: float, vol_regime: str = "unknown"):
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
        # Use IV/HV regime from decision_aids (ratio > 1.25); fallback only for extremely high absolute IV (>60%)
        iv_rich = vol_regime == "iv_rich" or (
            vol_regime in ("unknown", "iv_only") and opt.atm_iv and opt.atm_iv > 0.60
        )

        if not options_ok:
            og = None
            if stock_vs_opt_score < -0.2:
                note = "Options data degraded — stock-only path unless you verify chain at broker."
            else:
                note = "Options data missing or weak; stock is the default actionable lane."
            return InstrumentRecommendation.stock, og, note

        # IV elevated vs historical vol + not immediate earnings -> credit-style options umbrella
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
