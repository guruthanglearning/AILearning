"""Decision-support helpers: stock vs options framing, checklists, sizing hints."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from app.schemas.agents import (
    DecisionAids,
    DecisionChecklistItem,
    InstrumentPlayRow,
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

    return DecisionAids(
        summary_headline=headline,
        stock_vs_options_score=round(score, 3),
        checklist=checklist,
        instrument_plays=plays,
        volatility=vol_ctx,
        position_sizing=sizing,
        comparison_matrix=matrix,
        user_questions=questions,
    )
