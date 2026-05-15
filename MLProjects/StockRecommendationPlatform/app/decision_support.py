"""Decision-support helpers: stock vs options framing, checklists, sizing hints."""

from __future__ import annotations

import math
from datetime import date
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from app.schemas.agents import (
    AgentStatus,
    DecisionAids,
    DecisionChecklistItem,
    InstrumentPlayRow,
    OptionLeg,
    OptionLegType,
    OptionRight,
    OptionsMetricRow,
    OptionsOutput,
    PositionSizingHint,
    RiskProOutput,
    TechnicalsOutput,
    VolatilityContext,
)

if TYPE_CHECKING:
    from app.providers.base import MarketDataProvider


async def _hv_20d(symbol: str, provider: MarketDataProvider) -> float | None:
    try:
        h = await provider.get_price_history(symbol, "3mo")
        if h is None or h.empty or len(h) < 25:
            return None
        lr = np.log(h["Close"]).diff().dropna().tail(20)
        if len(lr) < 15:
            return None
        return float(lr.std() * math.sqrt(252))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Options metrics table helpers (§6)
# ---------------------------------------------------------------------------


def _calc_dte(expiry: str) -> int:
    try:
        return max(0, (date.fromisoformat(expiry) - date.today()).days)
    except Exception:
        return 0


def _degraded_row(template_id: str, strategy_label: str, spot: float | None, reasons: list[str]) -> OptionsMetricRow:
    return OptionsMetricRow(
        template_id=template_id,
        strategy_label=strategy_label,
        underlying_at_analysis=spot,
        row_data_quality="degraded",
        degraded_reasons=reasons,
    )


def _debit_call_spread_row(
    expiry: str,
    dte: int,
    spot: float,
    long_strike: float,
    long_ask: float,
    short_strike: float,
    short_bid: float,
    trend: str | None,
    liq_hint: str | None,
    imp_move_pct: float | None,
) -> OptionsMetricRow:
    width = round(short_strike - long_strike, 2)
    net_debit = round(long_ask - short_bid, 2)
    if net_debit <= 0 or net_debit >= width or width <= 0:
        return _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", spot, ["degenerate_spread_prices"])
    return OptionsMetricRow(
        template_id="bull_call_spread",
        strategy_label="Bull Call Spread (Debit Vertical)",
        expiration=expiry,
        dte_at_analysis=dte,
        legs=[
            OptionLeg(right=OptionRight.call, strike=long_strike, quantity_signed=1, leg_type=OptionLegType.long),
            OptionLeg(right=OptionRight.call, strike=short_strike, quantity_signed=-1, leg_type=OptionLegType.short),
        ],
        net_debit_credit=-net_debit,
        max_profit=round(width - net_debit, 2),
        max_loss=round(net_debit, 2),
        breakeven_prices=[round(long_strike + net_debit, 2)],
        underlying_at_analysis=spot,
        row_data_quality="full",
        trend_alignment="aligned" if (trend or "") == "bullish" else "neutral",
        liquidity=liq_hint or "unknown",
        risk_profile=f"Max loss ${net_debit:.2f} (net debit) per contract × 100",
        expected_move=f"±{imp_move_pct:.1f}% (1d straddle)" if imp_move_pct else None,
        management_rules="Close at +50% max profit or −100% max loss; no roll unless thesis intact",
    )


def _credit_put_spread_row(
    expiry: str,
    dte: int,
    spot: float,
    short_strike: float,
    short_bid: float,
    long_strike: float,
    long_ask: float,
    trend: str | None,
    liq_hint: str | None,
    imp_move_pct: float | None,
) -> OptionsMetricRow:
    width = round(short_strike - long_strike, 2)
    net_credit = round(short_bid - long_ask, 2)
    if net_credit <= 0 or net_credit >= width or width <= 0:
        return _degraded_row("short_put_spread", "Short Put Spread (Credit Vertical)", spot, ["degenerate_spread_prices"])
    return OptionsMetricRow(
        template_id="short_put_spread",
        strategy_label="Short Put Spread (Credit Vertical)",
        expiration=expiry,
        dte_at_analysis=dte,
        legs=[
            OptionLeg(right=OptionRight.put, strike=short_strike, quantity_signed=-1, leg_type=OptionLegType.short),
            OptionLeg(right=OptionRight.put, strike=long_strike, quantity_signed=1, leg_type=OptionLegType.long),
        ],
        net_debit_credit=net_credit,
        max_profit=round(net_credit, 2),
        max_loss=round(width - net_credit, 2),
        breakeven_prices=[round(short_strike - net_credit, 2)],
        underlying_at_analysis=spot,
        row_data_quality="full",
        trend_alignment="aligned" if (trend or "") in ("bullish", "mixed") else "counter",
        liquidity=liq_hint or "unknown",
        risk_profile=f"Max loss ${width - net_credit:.2f} per contract × 100",
        expected_move=f"±{imp_move_pct:.1f}% (1d straddle)" if imp_move_pct else None,
        management_rules="Close at +50% of max credit; defend at −200% of credit received",
    )


def _leg_mid(row: pd.Series) -> tuple[float, float]:
    """Return (bid, ask) for a chain row; 0.0 when missing."""
    bid = float(row["bid"]) if "bid" in row.index and pd.notna(row["bid"]) else 0.0
    ask = float(row["ask"]) if "ask" in row.index and pd.notna(row["ask"]) else 0.0
    return bid, ask


def _build_bull_call_spread(
    calls: pd.DataFrame | None,
    spot: float,
    expiry: str,
    dte: int,
    trend: str | None,
    liq: str | None,
    imp_move: float | None,
) -> OptionsMetricRow:
    if calls is None or calls.empty:
        return _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", spot, ["no_call_chain"])
    try:
        df = calls.copy()
        df["dist"] = (df["strike"] - spot).abs()
        atm = df.loc[df["dist"].idxmin()]
        atm_strike = float(atm["strike"])
        otm_candidates = df[df["strike"] > atm_strike + 0.5].sort_values("strike")
        if otm_candidates.empty:
            return _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", spot, ["no_otm_call_strike"])
        otm = otm_candidates.iloc[0]
        otm_strike = float(otm["strike"])
        atm_bid, atm_ask = _leg_mid(atm)
        otm_bid, otm_ask = _leg_mid(otm)
        quality = "full" if atm_ask > 0 and otm_bid > 0 else "partial"
        row = _debit_call_spread_row(expiry, dte, spot, atm_strike, atm_ask, otm_strike, otm_bid, trend, liq, imp_move)
        if quality == "partial" and row.row_data_quality == "full":
            row = row.model_copy(update={"row_data_quality": "partial", "degraded_reasons": ["zero_bid_ask_on_leg"]})
        return row
    except Exception as exc:
        return _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", spot, [str(exc)])


def _build_short_put_spread(
    puts: pd.DataFrame | None,
    spot: float,
    expiry: str,
    dte: int,
    trend: str | None,
    liq: str | None,
    imp_move: float | None,
) -> OptionsMetricRow:
    if puts is None or puts.empty:
        return _degraded_row("short_put_spread", "Short Put Spread (Credit Vertical)", spot, ["no_put_chain"])
    try:
        df = puts.copy()
        df["dist"] = (df["strike"] - spot).abs()
        atm = df.loc[df["dist"].idxmin()]
        atm_strike = float(atm["strike"])
        otm_candidates = df[df["strike"] < atm_strike - 0.5].sort_values("strike", ascending=False)
        if otm_candidates.empty:
            return _degraded_row("short_put_spread", "Short Put Spread (Credit Vertical)", spot, ["no_otm_put_strike"])
        otm = otm_candidates.iloc[0]
        otm_strike = float(otm["strike"])
        atm_bid, atm_ask = _leg_mid(atm)
        otm_bid, otm_ask = _leg_mid(otm)
        quality = "full" if atm_bid > 0 and otm_ask > 0 else "partial"
        row = _credit_put_spread_row(expiry, dte, spot, atm_strike, atm_bid, otm_strike, otm_ask, trend, liq, imp_move)
        if quality == "partial" and row.row_data_quality == "full":
            row = row.model_copy(update={"row_data_quality": "partial", "degraded_reasons": ["zero_bid_ask_on_leg"]})
        return row
    except Exception as exc:
        return _degraded_row("short_put_spread", "Short Put Spread (Credit Vertical)", spot, [str(exc)])


async def _build_options_metrics_table(
    symbol: str,
    spot: float | None,
    opt: OptionsOutput,
    tech: TechnicalsOutput,
    provider: MarketDataProvider,
) -> list[OptionsMetricRow]:
    summary = OptionsMetricRow(
        template_id="underlying_summary",
        strategy_label="Underlying Summary",
        underlying_at_analysis=spot,
        row_data_quality="full" if spot else "degraded",
        expiration=opt.nearest_expiry,
        expected_move=(f"±{opt.implied_move_1d_pct:.1f}% (1d)" if opt.implied_move_1d_pct else None),
        liquidity=opt.chain_liquidity_hint,
    )

    if spot is None or opt.status == AgentStatus.failed or not opt.nearest_expiry:
        return [
            summary,
            _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", spot, ["options_data_unavailable"]),
            _degraded_row("short_put_spread", "Short Put Spread (Credit Vertical)", spot, ["options_data_unavailable"]),
        ]

    try:
        chain_data = await provider.get_option_chain(symbol)
        calls: pd.DataFrame | None = chain_data.get("calls")
        puts: pd.DataFrame | None = chain_data.get("puts")
        expiry: str = chain_data.get("chosen_expiry") or opt.nearest_expiry
    except Exception as exc:
        return [
            summary,
            _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", spot, [f"chain_fetch_failed: {exc}"]),
            _degraded_row("short_put_spread", "Short Put Spread (Credit Vertical)", spot, [f"chain_fetch_failed: {exc}"]),
        ]

    dte = _calc_dte(expiry)
    trend = tech.trend_hint
    liq = opt.chain_liquidity_hint
    imp_move = opt.implied_move_1d_pct

    row_b = _build_bull_call_spread(calls, spot, expiry, dte, trend, liq, imp_move)
    row_c = _build_short_put_spread(puts, spot, expiry, dte, trend, liq, imp_move)
    return [summary, row_b, row_c]


async def build_decision_aids(
    symbol: str,
    last_price: float | None,
    tech: TechnicalsOutput,
    opt: OptionsOutput,
    risk: RiskProOutput,
    portfolio_value_usd: float | None,
    max_risk_pct: float | None,
    provider: MarketDataProvider,
    ml_forecast_signal: str | None = None,
) -> DecisionAids:
    trend = tech.trend_hint or "mixed"
    hv = await _hv_20d(symbol, provider)
    atm_iv = opt.atm_iv
    regime = "unknown"
    iv_note = None
    if atm_iv is not None and hv is not None and hv > 0:
        ratio = atm_iv / hv
        if ratio > 1.25:
            regime = "iv_rich"
            iv_note = "IV elevated vs recent realized vol — option sellers get more premium; buyers pay more."
        elif ratio < 0.85:
            regime = "iv_cheap"
            iv_note = "IV below recent realized vol — long premium structures relatively cheaper vs recent swings."
        else:
            regime = "iv_neutral"
            iv_note = "IV roughly in line with recent realized volatility."
    elif atm_iv is not None:
        regime = "iv_only"
        iv_note = "Historical vol unavailable; rely on chain and events."

    vol_ctx = VolatilityContext(
        regime=regime,
        atm_iv=atm_iv,
        hv_20d_annualized=hv,
        iv_vs_hv_note=iv_note,
        implied_move_1d_pct=opt.implied_move_1d_pct,
    )

    checklist: list[DecisionChecklistItem] = []

    def add_item(cid: str, label: str, state: str, explanation: str, weight: float = 1.0) -> None:
        checklist.append(
            DecisionChecklistItem(
                id=cid, label=label, state=state, weight=weight, explanation=explanation
            )
        )

    # Directional clarity from technicals
    if trend == "mixed":
        add_item(
            "dir",
            "Directional clarity",
            "warn",
            "Trend/momentum mixed — defined-risk options or smaller stock size often preferred.",
        )
    elif trend in ("bullish", "bearish"):
        add_item(
            "dir",
            "Directional clarity",
            "pass",
            f"Technicals lean {trend}; stock or directional options can be justified with a plan.",
        )
    else:
        add_item("dir", "Directional clarity", "warn", "No trend read.")

    # Earnings
    if risk.has_upcoming_earnings:
        add_item(
            "earn",
            "Earnings window",
            "warn",
            "Earnings soon — gap risk rises. Favor defined-risk options or reduce stock size.",
            weight=1.5,
        )
    else:
        add_item("earn", "Earnings window", "pass", "No imminent earnings flag from calendar feed.")

    # Options liquidity
    if opt.status.value == "failed" or opt.atm_iv is None:
        add_item(
            "opt_liq",
            "Options liquidity / data",
            "fail",
            "Options data weak — prefer stock unless you verify chain on your broker.",
        )
    elif opt.chain_liquidity_hint == "thin":
        add_item(
            "opt_liq",
            "Options liquidity / data",
            "warn",
            "Open interest looks thin — wider spreads; stock may be simpler.",
        )
    else:
        add_item("opt_liq", "Options liquidity / data", "pass", "Basic chain readability acceptable for screening.")

    if ml_forecast_signal and ml_forecast_signal != "Hold":
        aligned = (
            (ml_forecast_signal == "Buy" and trend == "bullish")
            or (ml_forecast_signal == "Sell" and trend == "bearish")
        )
        add_item(
            "ml_align",
            "ML forecast vs technicals",
            "pass" if aligned else "warn",
            f"StockPrediction-style signal: {ml_forecast_signal}. "
            f"Technicals: {trend}. Treat ML as one input only.",
            weight=0.5,
        )

    # Breakeven framing (conceptual, not a specific trade)
    if regime == "iv_rich":
        add_item(
            "vol",
            "Volatility regime vs structure",
            "pass",
            "IV rich — credit spreads / covered calls relatively attractive vs buying naked long calls.",
        )
    elif regime == "iv_cheap":
        add_item(
            "vol",
            "Volatility regime vs structure",
            "pass",
            "IV cheap vs realized — long stock or long-vol structures relatively less penalized.",
        )
    else:
        add_item(
            "vol",
            "Volatility regime vs structure",
            "warn",
            "Vol regime unclear — size smaller or use defined risk.",
        )

    # Score: +1 stock-heavy, -1 options-heavy (directional structures)
    score = 0.0
    wsum = 0.0
    for it in checklist:
        w = it.weight
        wsum += w
        if it.state == "pass":
            score += 0.25 * w
        elif it.state == "warn":
            score += 0.0
        else:
            score -= 0.35 * w
    if regime == "iv_rich":
        score -= 0.4
    elif regime == "iv_cheap":
        score += 0.25
    if risk.has_upcoming_earnings:
        score -= 0.35
    if opt.chain_liquidity_hint == "thin":
        score += 0.15
    score = max(-1.0, min(1.0, score / max(1.0, wsum * 0.25)))

    plays = [
        InstrumentPlayRow(
            play_id="long_stock",
            label="Long stock",
            when_favored="Clear directional view, want dividends/voting, simplest risk story.",
            max_risk_profile="Capital at risk up to your stop or full position.",
            capital_efficiency_note="100 shares tie more notional than a single long call.",
            complexity="low",
        ),
        InstrumentPlayRow(
            play_id="long_call",
            label="Long call (or put for bearish)",
            when_favored="Strong directional view, want capped loss, accept theta decay.",
            max_risk_profile="Defined: premium paid.",
            capital_efficiency_note="Higher leverage to deltas; IV matters — check regime.",
            complexity="medium",
        ),
        InstrumentPlayRow(
            play_id="vertical_spread",
            label="Debit vertical spread",
            when_favored="Directional with capped risk/reward; IV not extremely cheap.",
            max_risk_profile="Defined: net debit.",
            capital_efficiency_note="Often more capital-efficient than naked long option for same directional bet.",
            complexity="medium",
        ),
        InstrumentPlayRow(
            play_id="cash_secured_put",
            label="Cash-secured put / covered call",
            when_favored="Willing to own stock at strike (CSP) or sell upside (CC); income bias.",
            max_risk_profile="Stock assignment risk / upside capped for CC.",
            capital_efficiency_note="Works when IV rich and you accept stock handling.",
            complexity="medium",
        ),
    ]

    sizing: list[PositionSizingHint] = []
    if portfolio_value_usd and max_risk_pct and last_price and last_price > 0:
        risk_dollars = portfolio_value_usd * (max_risk_pct / 100.0)
        sizing.append(
            PositionSizingHint(
                instrument_type="stock",
                note="Illustrative: risk budget / distance-to-stop approximates share count ceiling.",
                example_notional_at_1pct_portfolio=portfolio_value_usd * 0.01,
            )
        )
        sizing.append(
            PositionSizingHint(
                instrument_type="options",
                note="Risk as max loss per spread or premium; keep per-trade risk a small fraction of portfolio.",
                suggested_risk_budget_pct_range=(0.25, 1.0),
                example_notional_at_1pct_portfolio=risk_dollars,
            )
        )

    matrix: dict[str, Any] = {
        "axes": ["capital_at_risk", "theta_vega_exposure", "gap_risk_earnings", "complexity"],
        "long_stock": {
            "capital_at_risk": "high",
            "theta_vega_exposure": "none",
            "gap_risk_earnings": "full",
            "complexity": "low",
        },
        "long_option": {
            "capital_at_risk": "capped_premium",
            "theta_vega_exposure": "high",
            "gap_risk_earnings": "vol_crush_risk",
            "complexity": "medium",
        },
        "spread": {
            "capital_at_risk": "capped_debit",
            "theta_vega_exposure": "moderate",
            "gap_risk_earnings": "moderate",
            "complexity": "medium",
        },
        "breakeven_thinking": {
            "stock": "Breakeven is current price; profit above +fees.",
            "long_call": "Spot must exceed strike + premium by expiry (all else equal).",
            "debit_spread": "Underlying must move enough to cover net debit; capped payoff.",
        },
    }

    questions = [
        "Is this trade speculative or part of a multi-month thesis?",
        "What invalidates the idea — price level, time, or vol event?",
        "Can you state max loss in dollars before entering?",
        "If assigned on a short put / covered call, is that acceptable?",
    ]

    headline = (
        "Lean stock / long shares or simple stock risk if clarity is high and options data is weak."
        if score > 0.35
        else "Lean options with defined risk if IV/liquidity supports structures and earnings risk is elevated."
        if score < -0.35
        else "Balanced — compare long stock vs debit spread vs long option using max loss and breakeven."
    )

    opts_table = await _build_options_metrics_table(symbol, last_price, opt, tech, provider)

    return DecisionAids(
        summary_headline=headline,
        stock_vs_options_score=round(score, 3),
        checklist=checklist,
        instrument_plays=plays,
        volatility=vol_ctx,
        position_sizing=sizing,
        comparison_matrix=matrix,
        user_questions=questions,
        options_metrics_table=opts_table,
    )
