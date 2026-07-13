"""Options metrics table tests — all offline (pure functions + schema only)."""
from __future__ import annotations

import pandas as pd
import pytest

from app.decision_support import (
    _build_bull_call_spread,
    _build_short_put_spread,
    _credit_put_spread_row,
    _debit_call_spread_row,
    _degraded_row,
)
from app.schemas.agents import (
    AgentStatus,
    DataProvenance,
    DecisionAids,
    OptionLegType,
    OptionRight,
    OptionsMetricRow,
    OptionsOutput,
)


def _prov() -> DataProvenance:
    return DataProvenance(source="test")


def _ok_opt(iv: float = 0.3, expiry: str = "2025-08-15") -> OptionsOutput:
    return OptionsOutput(
        agent_name="OptionsAgent",
        status=AgentStatus.complete,
        provenance=_prov(),
        atm_iv=iv,
        nearest_expiry=expiry,
        chain_liquidity_hint="adequate",
        implied_move_1d_pct=1.5,
    )


def _failed_opt() -> OptionsOutput:
    return OptionsOutput(
        agent_name="OptionsAgent",
        status=AgentStatus.failed,
        provenance=_prov(),
        chain_liquidity_hint="unknown",
    )


# ---------------------------------------------------------------------------
# Pure payoff math
# ---------------------------------------------------------------------------


def test_debit_call_spread_payoff_math():
    # long 150 call ask=4.00, short 155 call bid=1.50 → net_debit=2.50, width=5.00
    row = _debit_call_spread_row(
        expiry="2025-08-15", dte=92, spot=150.0,
        long_strike=150.0, long_ask=4.00,
        short_strike=155.0, short_bid=1.50,
        trend="bullish", liq_hint="adequate", imp_move_pct=1.5,
    )
    assert row.template_id == "bull_call_spread"
    assert row.row_data_quality == "full"
    assert row.net_debit_credit == pytest.approx(-2.50)
    assert row.max_loss == pytest.approx(2.50)
    assert row.max_profit == pytest.approx(2.50)         # width(5) - debit(2.5)
    assert row.breakeven_prices == [pytest.approx(152.50)]  # 150 + 2.50
    assert len(row.legs) == 2
    assert row.legs[0].right == OptionRight.call
    assert row.legs[0].leg_type == OptionLegType.long
    assert row.legs[1].leg_type == OptionLegType.short


def test_credit_put_spread_payoff_math():
    # short 150 put bid=3.00, long 145 put ask=1.20 → net_credit=1.80, width=5.00
    row = _credit_put_spread_row(
        expiry="2025-08-15", dte=92, spot=152.0,
        short_strike=150.0, short_bid=3.00,
        long_strike=145.0, long_ask=1.20,
        trend="bullish", liq_hint="adequate", imp_move_pct=1.5,
    )
    assert row.template_id == "short_put_spread"
    assert row.row_data_quality == "full"
    assert row.net_debit_credit == pytest.approx(1.80)
    assert row.max_profit == pytest.approx(1.80)
    assert row.max_loss == pytest.approx(3.20)           # width(5) - credit(1.80)
    assert row.breakeven_prices == [pytest.approx(148.20)]  # 150 - 1.80
    assert len(row.legs) == 2
    assert row.legs[0].right == OptionRight.put
    assert row.legs[0].leg_type == OptionLegType.short
    assert row.legs[1].leg_type == OptionLegType.long


def test_degenerate_debit_spread_returns_degraded():
    # net_debit >= width → degenerate
    row = _debit_call_spread_row(
        expiry="2025-08-15", dte=92, spot=150.0,
        long_strike=150.0, long_ask=6.00,   # expensive long leg
        short_strike=153.0, short_bid=1.00,  # width=3, net_debit=5 >= width
        trend=None, liq_hint=None, imp_move_pct=None,
    )
    assert row.row_data_quality == "degraded"
    assert len(row.legs) == 0
    assert len(row.breakeven_prices) == 0
    assert "degenerate_spread_prices" in row.degraded_reasons


def test_degenerate_credit_spread_returns_degraded():
    # net_credit <= 0 → degenerate
    row = _credit_put_spread_row(
        expiry="2025-08-15", dte=92, spot=150.0,
        short_strike=150.0, short_bid=1.00,
        long_strike=145.0, long_ask=2.00,   # long leg more expensive than short
        trend=None, liq_hint=None, imp_move_pct=None,
    )
    assert row.row_data_quality == "degraded"
    assert len(row.legs) == 0
    assert len(row.breakeven_prices) == 0


# ---------------------------------------------------------------------------
# Underlying summary / degraded path
# ---------------------------------------------------------------------------


def test_underlying_summary_always_first():
    row = _degraded_row("underlying_summary", "Underlying Summary", 150.0, [])
    assert row.template_id == "underlying_summary"
    assert row.underlying_at_analysis == 150.0
    assert row.legs == []
    assert row.breakeven_prices == []


def test_degraded_row_has_no_breakevens_or_legs():
    row = _degraded_row("bull_call_spread", "Bull Call Spread (Debit Vertical)", None, ["options_data_unavailable"])
    assert row.row_data_quality == "degraded"
    assert row.legs == []
    assert row.breakeven_prices == []
    assert row.max_profit is None
    assert row.max_loss is None


# ---------------------------------------------------------------------------
# Market-closed relabelling
# ---------------------------------------------------------------------------


def _zero_bid_ask_calls(spot: float) -> pd.DataFrame:
    return pd.DataFrame({
        "strike": [spot - 5, spot, spot + 5, spot + 10],
        "bid": [0.0, 0.0, 0.0, 0.0],
        "ask": [0.0, 0.0, 0.0, 0.0],
        "impliedVolatility": [0.30, 0.28, 0.26, 0.24],
        "openInterest": [100, 200, 150, 80],
        "lastPrice": [5.0, 3.0, 1.5, 0.5],
    })


def _zero_bid_ask_puts(spot: float) -> pd.DataFrame:
    return pd.DataFrame({
        "strike": [spot - 10, spot - 5, spot, spot + 5],
        "bid": [0.0, 0.0, 0.0, 0.0],
        "ask": [0.0, 0.0, 0.0, 0.0],
        "impliedVolatility": [0.24, 0.26, 0.28, 0.30],
        "openInterest": [80, 150, 200, 100],
        "lastPrice": [0.5, 1.5, 3.0, 5.0],
    })


def test_market_closed_tagging_bull_call_spread():
    calls = _zero_bid_ask_calls(spot=150.0)
    row = _build_bull_call_spread(calls, 150.0, "2025-08-15", 30, "bullish", "adequate", 1.5, market_state="CLOSED")
    assert row.row_data_quality == "degraded"
    assert "market_closed" in row.degraded_reasons
    assert "degenerate_spread_prices" not in row.degraded_reasons


def test_market_closed_tagging_short_put_spread():
    puts = _zero_bid_ask_puts(spot=150.0)
    row = _build_short_put_spread(puts, 150.0, "2025-08-15", 30, "bullish", "adequate", 1.5, market_state="CLOSED")
    assert row.row_data_quality == "degraded"
    assert "market_closed" in row.degraded_reasons
    assert "degenerate_spread_prices" not in row.degraded_reasons


def test_pre_market_tagging_bull_call_spread():
    calls = _zero_bid_ask_calls(spot=150.0)
    row = _build_bull_call_spread(calls, 150.0, "2025-08-15", 30, "bullish", "adequate", 1.5, market_state="PRE")
    assert "market_closed" in row.degraded_reasons


def test_regular_hours_keeps_degenerate_reason():
    """During REGULAR hours, zero bid/ask is a real data problem — keep original label."""
    calls = _zero_bid_ask_calls(spot=150.0)
    row = _build_bull_call_spread(calls, 150.0, "2025-08-15", 30, "bullish", "adequate", 1.5, market_state="REGULAR")
    assert "degenerate_spread_prices" in row.degraded_reasons
    assert "market_closed" not in row.degraded_reasons


def test_unknown_market_state_keeps_degenerate_reason():
    """When market_state is None (unknown), preserve original reason to avoid hiding real errors."""
    calls = _zero_bid_ask_calls(spot=150.0)
    row = _build_bull_call_spread(calls, 150.0, "2025-08-15", 30, "bullish", "adequate", 1.5, market_state=None)
    assert "degenerate_spread_prices" in row.degraded_reasons
    assert "market_closed" not in row.degraded_reasons


# ---------------------------------------------------------------------------
# Schema integration
# ---------------------------------------------------------------------------


def test_options_metrics_table_field_on_decision_aids():
    row = OptionsMetricRow(
        template_id="underlying_summary",
        strategy_label="Underlying Summary",
        row_data_quality="full",
    )
    aids = DecisionAids(
        summary_headline="test",
        stock_vs_options_score=0.0,
        options_metrics_table=[row],
    )
    assert len(aids.options_metrics_table) == 1
    assert aids.options_metrics_table[0].template_id == "underlying_summary"
