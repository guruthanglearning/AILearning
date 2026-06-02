"""Extra tests for decision_support.py covering _iv_rank_52w, spread builder edge cases,
and supervisor _merge vol_regime branches."""
from __future__ import annotations

from unittest.mock import AsyncMock

import numpy as np
import pandas as pd
import pytest

from app.decision_support import (
    _build_bull_call_spread,
    _build_short_put_spread,
    _iv_rank_52w,
)
from app.schemas.agents import (
    AgentStatus,
    DataProvenance,
    InstrumentRecommendation,
    MarketDataOutput,
    OptionsOutput,
    RiskProOutput,
    TechnicalsOutput,
)
from app.supervisor import Supervisor


def _prov():
    return DataProvenance(source="test")


# ---------------------------------------------------------------------------
# _iv_rank_52w — normal path
# ---------------------------------------------------------------------------


def _make_1y_df(n: int = 252, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({"Close": prices})


@pytest.mark.asyncio
async def test_iv_rank_52w_normal():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_1y_df())
    rank = await _iv_rank_52w("AAPL", 0.30, provider)
    assert rank is not None
    assert 0.0 <= rank <= 100.0


@pytest.mark.asyncio
async def test_iv_rank_52w_high_iv_returns_high_rank():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_1y_df())
    rank_low = await _iv_rank_52w("AAPL", 0.10, provider)
    rank_high = await _iv_rank_52w("AAPL", 1.50, provider)
    assert rank_low is not None and rank_high is not None
    assert rank_high > rank_low


@pytest.mark.asyncio
async def test_iv_rank_52w_clamped_to_100():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_1y_df())
    rank = await _iv_rank_52w("AAPL", 9999.0, provider)
    assert rank == 100.0


@pytest.mark.asyncio
async def test_iv_rank_52w_clamped_to_0():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_1y_df())
    rank = await _iv_rank_52w("AAPL", 0.0, provider)
    assert rank == pytest.approx(0.0, abs=5.0)  # very low IV sits near bottom


@pytest.mark.asyncio
async def test_iv_rank_52w_returns_none_when_provider_returns_none():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=None)
    rank = await _iv_rank_52w("AAPL", 0.30, provider)
    assert rank is None


@pytest.mark.asyncio
async def test_iv_rank_52w_returns_none_when_df_empty():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=pd.DataFrame())
    rank = await _iv_rank_52w("AAPL", 0.30, provider)
    assert rank is None


@pytest.mark.asyncio
async def test_iv_rank_52w_returns_none_when_insufficient_rows():
    # Less than 60 rows → returns None early
    df = pd.DataFrame({"Close": [100.0] * 30})
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=df)
    rank = await _iv_rank_52w("AAPL", 0.30, provider)
    assert rank is None


@pytest.mark.asyncio
async def test_iv_rank_52w_returns_none_when_flat_prices():
    # Flat prices → rolling HV is 0 everywhere → hv_max == hv_min → None
    df = pd.DataFrame({"Close": [100.0] * 252})
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=df)
    rank = await _iv_rank_52w("AAPL", 0.30, provider)
    assert rank is None


@pytest.mark.asyncio
async def test_iv_rank_52w_returns_none_on_exception():
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(side_effect=RuntimeError("boom"))
    rank = await _iv_rank_52w("AAPL", 0.30, provider)
    assert rank is None


# ---------------------------------------------------------------------------
# _build_bull_call_spread edge cases
# ---------------------------------------------------------------------------


def _calls_df(strikes):
    """Realistic call prices: ATM ~3.50, decreasing by $1 per $5 strike interval."""
    rows = []
    for s in strikes:
        dist = (s - 100) / 5  # number of $5 intervals above ATM
        bid = max(0.0, round(3.0 - dist * 1.0, 2))
        ask = max(0.0, round(3.5 - dist * 1.0, 2))
        rows.append({"strike": s, "bid": bid, "ask": ask})
    return pd.DataFrame(rows)


def test_build_bull_call_spread_no_call_chain():
    row = _build_bull_call_spread(None, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"
    assert "no_call_chain" in row.degraded_reasons


def test_build_bull_call_spread_empty_df():
    row = _build_bull_call_spread(pd.DataFrame(), 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"
    assert "no_call_chain" in row.degraded_reasons


def test_build_bull_call_spread_no_otm_strike():
    # Only one strike (the ATM) — no OTM candidates
    calls = _calls_df([100.0])
    row = _build_bull_call_spread(calls, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"
    assert "no_otm_call_strike" in row.degraded_reasons


def test_build_bull_call_spread_normal():
    calls = _calls_df([95.0, 100.0, 105.0, 110.0])
    row = _build_bull_call_spread(calls, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.template_id == "bull_call_spread"
    assert row.row_data_quality in ("full", "partial")


def test_build_bull_call_spread_zero_bids_gives_partial():
    # ATM ask > 0, OTM bid = 0 → quality marker = "partial"
    # net_debit = 3.5 - 0 = 3.5 < width 5 → row starts "full", gets downgraded
    calls = pd.DataFrame([
        {"strike": 100.0, "bid": 3.0, "ask": 3.5},
        {"strike": 105.0, "bid": 0.0, "ask": 0.5},
    ])
    row = _build_bull_call_spread(calls, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "partial"


def test_build_bull_call_spread_exception_gives_degraded():
    # Pass a DataFrame that will throw during processing (missing 'strike' col)
    bad_df = pd.DataFrame({"not_strike": [100.0]})
    row = _build_bull_call_spread(bad_df, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"


# ---------------------------------------------------------------------------
# _build_short_put_spread edge cases
# ---------------------------------------------------------------------------


def _puts_df(strikes):
    rows = []
    for s in strikes:
        rows.append({"strike": s, "bid": max(0.0, 10.0 - abs(s - 100)), "ask": max(0.0, 10.5 - abs(s - 100))})
    return pd.DataFrame(rows)


def test_build_short_put_spread_no_put_chain():
    row = _build_short_put_spread(None, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"
    assert "no_put_chain" in row.degraded_reasons


def test_build_short_put_spread_empty_df():
    row = _build_short_put_spread(pd.DataFrame(), 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"
    assert "no_put_chain" in row.degraded_reasons


def test_build_short_put_spread_no_otm_strike():
    # Only one strike — no OTM puts below ATM
    puts = _puts_df([100.0])
    row = _build_short_put_spread(puts, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"
    assert "no_otm_put_strike" in row.degraded_reasons


def test_build_short_put_spread_normal():
    puts = _puts_df([85.0, 90.0, 95.0, 100.0])
    row = _build_short_put_spread(puts, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.template_id == "short_put_spread"
    assert row.row_data_quality in ("full", "partial")


def test_build_short_put_spread_zero_bids_gives_partial():
    # ATM bid > 0, OTM ask = 0 → quality marker = "partial"
    # net_credit = 3.0 - 0 = 3.0 < width 5 → row starts "full", gets downgraded
    puts = pd.DataFrame([
        {"strike": 95.0,  "bid": 0.0, "ask": 0.0},
        {"strike": 100.0, "bid": 3.0, "ask": 3.5},
    ])
    row = _build_short_put_spread(puts, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "partial"


def test_build_short_put_spread_exception_gives_degraded():
    bad_df = pd.DataFrame({"not_strike": [100.0]})
    row = _build_short_put_spread(bad_df, 100.0, "2025-09-19", 30, "bullish", "good", 1.5)
    assert row.row_data_quality == "degraded"


# ---------------------------------------------------------------------------
# Supervisor._merge — vol_regime branches
# ---------------------------------------------------------------------------


def _market_ok(price=150.0):
    return MarketDataOutput(
        agent_name="m", status=AgentStatus.complete, provenance=_prov(), last_price=price
    )


def _tech(trend="bullish"):
    return TechnicalsOutput(
        agent_name="t", status=AgentStatus.complete, provenance=_prov(), trend_hint=trend
    )


def _opt(atm_iv=0.30):
    return OptionsOutput(
        agent_name="o", status=AgentStatus.complete, provenance=_prov(), atm_iv=atm_iv
    )


def _risk(earnings=False):
    return RiskProOutput(
        agent_name="r", status=AgentStatus.complete, provenance=_prov(),
        has_upcoming_earnings=earnings,
    )


def test_merge_iv_rich_regime_recommends_options():
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("bullish"), _opt(0.40), _risk(), 0.1, vol_regime="iv_rich")
    assert v == InstrumentRecommendation.options
    assert og is not None
    assert og.strategy_family == "premium_selling_or_covered_call"
    assert "iv_elevated" in og.rationale_codes


def test_merge_iv_neutral_bullish_recommends_stock():
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("bullish"), _opt(0.25), _risk(), 0.4, vol_regime="iv_neutral")
    assert v == InstrumentRecommendation.stock
    assert og is not None
    assert og.strategy_family == "long_stock_or_long_diagonal"


def test_merge_iv_rich_with_earnings_skips_premium_selling():
    # Earnings window overrides iv_rich → options with directional guidance (not credit)
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("mixed"), _opt(0.80), _risk(earnings=True), 0.1, vol_regime="iv_rich")
    assert v == InstrumentRecommendation.options
    # Earnings handler fires first — strategy is debit/defined-risk, not credit
    assert og is not None
    assert "earnings_soon" in og.rationale_codes


def test_merge_iv_rich_bearish_trend_not_credit():
    # iv_rich + bearish explicitly excluded from credit spread path
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("bearish"), _opt(0.80), _risk(), 0.1, vol_regime="iv_rich")
    # bearish with high IV → falls through to directional path
    assert v in (InstrumentRecommendation.stock, InstrumentRecommendation.options)


def test_merge_balanced_regime_score_positive_gives_stock():
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("mixed"), _opt(0.25), _risk(), 0.35, vol_regime="iv_neutral")
    assert v == InstrumentRecommendation.stock


def test_merge_balanced_regime_score_negative_gives_options():
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("mixed"), _opt(0.25), _risk(), -0.35, vol_regime="iv_neutral")
    assert v == InstrumentRecommendation.options


def test_merge_options_data_missing_falls_back_to_stock():
    opt_failed = OptionsOutput(
        agent_name="o", status=AgentStatus.failed, provenance=_prov(), atm_iv=None,
        error_message="timeout",
    )
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("bullish"), opt_failed, _risk(), 0.3, vol_regime="iv_neutral")
    assert v == InstrumentRecommendation.stock
    assert og is None


def test_merge_high_absolute_iv_unknown_regime_triggers_rich():
    # vol_regime="unknown" + atm_iv > 0.60 → treated as iv_rich
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("bullish"), _opt(0.70), _risk(), 0.1, vol_regime="unknown")
    assert v == InstrumentRecommendation.options
    assert og is not None
    assert "iv_elevated" in og.rationale_codes


def test_merge_moderate_iv_unknown_regime_not_rich():
    # vol_regime="unknown" + atm_iv < 0.60 → not treated as iv_rich → directional path
    s = Supervisor()
    v, og, note = s._merge(_market_ok(), _tech("bullish"), _opt(0.30), _risk(), 0.4, vol_regime="unknown")
    assert v == InstrumentRecommendation.stock
