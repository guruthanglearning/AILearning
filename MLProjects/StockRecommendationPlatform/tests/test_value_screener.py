"""Tests for the professional-grade value screener: sector-relative percentile
ranking, the EV/EBITDA-based Magic-Formula-style scoring function, the Graham
Number margin-of-safety anchor, and /v1/value/sectors end to end."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from app.limiter import limiter
from app.main import (
    _MOMENTUM_UNIVERSE,
    _SECTOR_ETFS,
    _compute_value_score_pro,
    _fetch_stock_raw,
    _graham_number_and_margin,
    _percentile_ranks,
    _percentile_ranks_by_group,
    _value_score_breakdown,
    _value_trend_signal,
    app,
)


@pytest.fixture(autouse=True)
def _patch_lifespan_deps(monkeypatch):
    monkeypatch.setattr("app.db.session.init_engine", lambda: None)
    monkeypatch.setattr("app.observability.configure_otel", lambda: None)
    monkeypatch.setattr("app.main.configure_otel", lambda: None)


@pytest.fixture(autouse=True)
def _no_history_download(monkeypatch):
    # The value endpoint batch-downloads 6 months of prices for the trend guard;
    # keep endpoint tests offline — individual tests override this when needed.
    monkeypatch.setattr("app.main._fetch_universe_history", lambda: None)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


# ---------------------------------------------------------------------------
# _compute_value_score_pro — pure scoring function
# ---------------------------------------------------------------------------


def test_value_score_none_when_no_percentiles_available():
    score = _compute_value_score_pro(None, None, None, None, None, None, None, None, None, None)
    assert score is None


def test_value_score_cheap_and_high_quality_scores_high():
    score = _compute_value_score_pro(
        pct_earnings_yield=90.0,
        pct_book_yield=90.0,
        pct_fcf_yield=90.0,
        pct_sales_yield=90.0,
        pct_peg_inv=90.0,
        pct_dividend=90.0,
        return_on_assets_pct=20.0,   # > 15% -> +5
        current_ratio=2.0,          # >= 1.5 -> +3
        fcf_to_net_income=1.2,      # >= 1.0 -> +4
        debt_to_equity_pct=30.0,    # < 50% -> +3
    )
    assert score is not None
    assert score == pytest.approx(0.90 * 0.85 * 100 + 15.0, abs=0.2)
    assert score <= 100.0


def test_value_score_expensive_and_weak_quality_scores_low():
    score = _compute_value_score_pro(
        pct_earnings_yield=5.0,
        pct_book_yield=5.0,
        pct_fcf_yield=5.0,
        pct_sales_yield=5.0,
        pct_peg_inv=5.0,
        pct_dividend=5.0,
        return_on_assets_pct=-2.0,     # unprofitable -> no bonus
        current_ratio=0.5,            # weak liquidity -> no bonus
        fcf_to_net_income=0.3,        # earnings not cash-backed -> no bonus
        debt_to_equity_pct=250.0,     # overleveraged -> no bonus + penalty
    )
    assert score is not None
    assert score < 10.0  # cheapness pool near 0 and penalty applied
    assert score >= 0.0  # clamped, never negative


def test_value_score_overleverage_penalty_reduces_score():
    base_kwargs = dict(
        pct_earnings_yield=50.0,
        pct_book_yield=50.0,
        pct_fcf_yield=50.0,
        pct_sales_yield=50.0,
        pct_peg_inv=50.0,
        pct_dividend=50.0,
        return_on_assets_pct=10.0,
        current_ratio=1.2,
        fcf_to_net_income=0.8,
    )
    moderate_debt = _compute_value_score_pro(**base_kwargs, debt_to_equity_pct=80.0)
    overleveraged = _compute_value_score_pro(**base_kwargs, debt_to_equity_pct=250.0)
    assert moderate_debt is not None and overleveraged is not None
    assert overleveraged < moderate_debt


def test_value_score_renormalizes_with_partial_percentiles():
    # Only earnings-yield percentile available — should still produce a score
    # based on that single factor renormalized to the full cheapness pool.
    score = _compute_value_score_pro(
        pct_earnings_yield=100.0,
        pct_book_yield=None,
        pct_fcf_yield=None,
        pct_sales_yield=None,
        pct_peg_inv=None,
        pct_dividend=None,
        return_on_assets_pct=None,
        current_ratio=None,
        fcf_to_net_income=None,
        debt_to_equity_pct=None,
    )
    assert score is not None
    assert score == pytest.approx(85.0, abs=0.2)


def test_value_score_clamped_to_100():
    score = _compute_value_score_pro(
        pct_earnings_yield=100.0,
        pct_book_yield=100.0,
        pct_fcf_yield=100.0,
        pct_sales_yield=100.0,
        pct_peg_inv=100.0,
        pct_dividend=100.0,
        return_on_assets_pct=50.0,
        current_ratio=3.0,
        fcf_to_net_income=2.0,
        debt_to_equity_pct=0.0,
    )
    assert score == 100.0


def test_value_score_negative_debt_to_equity_is_penalized_not_rewarded():
    """Negative Debt/Equity means negative shareholder equity (balance-sheet
    stress), not "low debt" — it must not earn the conservative-financing bonus."""
    base_kwargs = dict(
        pct_earnings_yield=50.0,
        pct_book_yield=50.0,
        pct_fcf_yield=50.0,
        pct_sales_yield=50.0,
        pct_peg_inv=50.0,
        pct_dividend=50.0,
        return_on_assets_pct=10.0,
        current_ratio=1.2,
        fcf_to_net_income=0.8,
    )
    healthy_debt = _compute_value_score_pro(**base_kwargs, debt_to_equity_pct=30.0)
    negative_equity = _compute_value_score_pro(**base_kwargs, debt_to_equity_pct=-300.0)
    zero_debt = _compute_value_score_pro(**base_kwargs, debt_to_equity_pct=0.0)
    assert negative_equity < healthy_debt
    assert negative_equity < zero_debt


def test_value_score_breakdown_parts_sum_to_score():
    score, cheap, quality, penalty = _value_score_breakdown(
        pct_earnings_yield=60.0, pct_book_yield=60.0, pct_fcf_yield=60.0,
        pct_sales_yield=60.0, pct_peg_inv=60.0, pct_dividend=60.0,
        return_on_assets_pct=10.0,  # +3
        current_ratio=1.2,          # +1
        fcf_to_net_income=0.8,      # +2
        debt_to_equity_pct=250.0,   # no D/E points, -5 penalty
    )
    assert cheap == pytest.approx(51.0)
    assert quality == 6.0
    assert penalty == -5.0
    assert score == pytest.approx(cheap + quality + penalty)


def test_value_score_breakdown_none_when_no_percentiles():
    assert _value_score_breakdown(None, None, None, None, None, None, None, None, None, None) is None


def test_compute_value_score_pro_matches_breakdown_score():
    kwargs = dict(
        pct_earnings_yield=80.0, pct_book_yield=None, pct_fcf_yield=70.0,
        pct_sales_yield=None, pct_peg_inv=50.0, pct_dividend=None,
        return_on_assets_pct=20.0, current_ratio=2.0, fcf_to_net_income=1.1,
        debt_to_equity_pct=30.0,
    )
    assert _compute_value_score_pro(**kwargs) == _value_score_breakdown(**kwargs)[0]


# ---------------------------------------------------------------------------
# _value_trend_signal — value + momentum falling-knife guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ret_6m", "price", "sma200", "expected"),
    [
        (0.10, 110.0, 100.0, "up"),
        (-0.10, 90.0, 100.0, "down"),
        (0.10, 90.0, 100.0, "mixed"),
        (-0.10, 110.0, 100.0, "mixed"),
        (0.0, None, None, "up"),        # flat 6M return alone counts as not falling
        (None, 90.0, 100.0, "down"),    # SMA alone decides when no history
        (None, None, None, None),
        (None, 90.0, 0.0, None),        # bad SMA ignored
    ],
)
def test_value_trend_signal(ret_6m, price, sma200, expected):
    assert _value_trend_signal(ret_6m, price, sma200) == expected


# ---------------------------------------------------------------------------
# _percentile_ranks — tie handling
# ---------------------------------------------------------------------------


def test_percentile_ranks_identical_values_share_the_same_rank():
    ranks = _percentile_ranks([5.0] * 10)
    assert all(r == 50.0 for r in ranks)


def test_percentile_ranks_partial_ties_get_average_rank():
    # [10, 20, 20, 30] -> the two 20s tie for ranks 1 and 2 (0-indexed), average rank 1.5
    ranks = _percentile_ranks([10.0, 20.0, 20.0, 30.0])
    assert ranks[0] == pytest.approx(0.0)
    assert ranks[1] == ranks[2] == pytest.approx(50.0)
    assert ranks[3] == pytest.approx(100.0)


def test_percentile_ranks_none_values_excluded_from_ranking():
    ranks = _percentile_ranks([10.0, None, 30.0])
    assert ranks[1] is None
    assert ranks[0] < ranks[2]


# ---------------------------------------------------------------------------
# _percentile_ranks_by_group — sector-relative ranking
# ---------------------------------------------------------------------------


def test_percentile_ranks_by_group_isolates_groups():
    # Group A's values are ~100x smaller than Group B's. Under a single global
    # ranking, Group A would be crushed toward 0. Grouped, each is ranked only
    # against its own peers.
    values = [1.0, 2.0, 100.0, 200.0]
    groups = ["A", "A", "B", "B"]
    ranks = _percentile_ranks_by_group(values, groups)
    assert ranks == [0.0, 100.0, 0.0, 100.0]


def test_percentile_ranks_by_group_none_group_excluded():
    values = [1.0, 2.0, 3.0]
    groups = ["A", None, "A"]
    ranks = _percentile_ranks_by_group(values, groups)
    assert ranks[1] is None
    assert ranks[0] == 0.0
    assert ranks[2] == 100.0


# ---------------------------------------------------------------------------
# _graham_number_and_margin — absolute intrinsic-value anchor
# ---------------------------------------------------------------------------


def test_graham_number_and_margin_basic():
    graham, margin = _graham_number_and_margin(trailing_eps=5.0, book_value_per_share=20.0, price=80.0)
    expected_graham = (22.5 * 5.0 * 20.0) ** 0.5
    assert graham == pytest.approx(expected_graham, abs=0.01)
    assert margin == pytest.approx((expected_graham - 80.0) / 80.0 * 100.0, abs=0.1)


def test_graham_number_none_when_eps_non_positive():
    assert _graham_number_and_margin(trailing_eps=-1.0, book_value_per_share=20.0, price=80.0) == (None, None)


def test_graham_number_none_when_book_value_non_positive():
    assert _graham_number_and_margin(trailing_eps=5.0, book_value_per_share=0.0, price=80.0) == (None, None)


def test_graham_number_margin_none_when_price_missing():
    graham, margin = _graham_number_and_margin(trailing_eps=5.0, book_value_per_share=20.0, price=None)
    assert graham is not None
    assert margin is None


# ---------------------------------------------------------------------------
# _fetch_stock_raw — PEG fallback
# ---------------------------------------------------------------------------


def test_fetch_stock_raw_falls_back_to_trailing_peg_ratio(monkeypatch):
    ticker = MagicMock()
    ticker.info = {"pegRatio": None, "trailingPegRatio": 1.42}
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    data = _fetch_stock_raw("TEST")
    assert data["peg_ratio"] == 1.42


def test_fetch_stock_raw_prefers_peg_ratio_when_present(monkeypatch):
    ticker = MagicMock()
    ticker.info = {"pegRatio": 2.0, "trailingPegRatio": 1.42}
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    data = _fetch_stock_raw("TEST")
    assert data["peg_ratio"] == 2.0


# ---------------------------------------------------------------------------
# /v1/value/sectors — endpoint
# ---------------------------------------------------------------------------


def _mock_value_ticker(**overrides) -> MagicMock:
    ticker = MagicMock()
    info = {
        "shortName": "Mock Co",
        "sector": "Technology",
        "industry": "Software",
        "currentPrice": 100.0,
        "regularMarketPrice": 100.0,
        "regularMarketChangePercent": 1.5,
        "marketCap": 50_000_000_000,
        "fiftyTwoWeekHigh": 120.0,
        "fiftyTwoWeekLow": 80.0,
        "fiftyDayAverage": 95.0,
        "twoHundredDayAverage": 90.0,
        "trailingPE": 15.0,
        "forwardPE": 13.0,
        "priceToBook": 2.0,
        "priceToSalesTrailing12Months": 3.0,
        "enterpriseToEbitda": 8.0,
        "enterpriseValue": 55_000_000_000,
        "pegRatio": 1.2,
        "dividendYield": 1.8,
        "debtToEquity": 40.0,
        "currentRatio": 1.5,
        "returnOnAssets": 0.10,
        "freeCashflow": 2_500_000_000,
        "netIncomeToCommon": 2_000_000_000,
        "bookValue": 20.0,
        "trailingEps": 5.0,
    }
    info.update(overrides)
    ticker.info = info
    return ticker


def test_value_sectors_endpoint_returns_all_universe_sectors(monkeypatch):
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_value_ticker())

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sectors"]) == len(_MOMENTUM_UNIVERSE)
    sector_names = {s["sector"] for s in data["sectors"]}
    assert sector_names == set(_MOMENTUM_UNIVERSE.keys())

    tech = next(s for s in data["sectors"] if s["sector"] == "Technology")
    assert len(tech["stocks"]) <= 5
    row = tech["stocks"][0]
    assert row["value_score"] is not None
    assert row["pe_ratio"] == 15.0
    assert row["ev_to_ebitda"] == 8.0
    assert row["price_to_sales"] == 3.0
    assert row["dividend_yield_pct"] == 1.8
    assert row["debt_to_equity_pct"] == 40.0
    assert row["return_on_assets_pct"] == pytest.approx(10.0)
    assert row["current_ratio"] == 1.5
    assert row["fcf_to_net_income"] == pytest.approx(1.25)
    assert row["graham_number"] is not None
    assert row["margin_of_safety_pct"] is not None


def test_value_sectors_rows_sorted_by_score_descending(monkeypatch):
    # Give every symbol identical fundamentals except EV/EBITDA so scores differ
    # deterministically (EV/EBITDA now drives the primary cheapness factor).
    def _ticker(sym: str) -> MagicMock:
        ev_ebitda = 4.0 if sym in ("AAPL", "MSFT") else 20.0
        return _mock_value_ticker(enterpriseToEbitda=ev_ebitda)

    monkeypatch.setattr("app.main.yf.Ticker", _ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=10")

    assert resp.status_code == 200
    tech = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")
    scores = [r["value_score"] for r in tech["stocks"] if r["value_score"] is not None]
    assert scores == sorted(scores, reverse=True)
    # The two cheap-EV/EBITDA stocks should clearly outrank the rest of the sector.
    top2 = {r["symbol"] for r in tech["stocks"][:2]}
    assert top2 == {"AAPL", "MSFT"}


def test_value_sectors_etf_metadata_present(monkeypatch):
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_value_ticker())

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    assert resp.status_code == 200
    tech = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")
    assert tech["etf_symbol"] == _SECTOR_ETFS["Technology"]
    assert tech["etf_price"] == 100.0


def _mock_bank_ticker() -> MagicMock:
    """Mirrors a real bank's yfinance .info — EBITDA/FCF/current-ratio are None
    because they aren't meaningful for financial institutions' balance sheets,
    confirmed against real JPM/BAC-style data."""
    ticker = MagicMock()
    ticker.info = {
        "shortName": "Mock Bank",
        "sector": "Financials",
        "industry": "Banks",
        "currentPrice": 150.0,
        "regularMarketPrice": 150.0,
        "regularMarketChangePercent": 0.5,
        "marketCap": 400_000_000_000,
        "fiftyTwoWeekHigh": 180.0,
        "fiftyTwoWeekLow": 120.0,
        "trailingPE": 12.0,
        "forwardPE": 11.0,
        "priceToBook": 1.8,
        "priceToSalesTrailing12Months": 4.0,
        "enterpriseToEbitda": None,
        "enterpriseValue": None,
        "pegRatio": 1.5,
        "dividendYield": 2.5,
        "debtToEquity": None,
        "currentRatio": None,
        "returnOnAssets": 0.013,
        "freeCashflow": None,
        "netIncomeToCommon": 60_000_000_000,
        "bookValue": 130.0,
        "trailingEps": 23.0,
    }
    return ticker


def test_value_sectors_handles_bank_like_missing_fields_gracefully(monkeypatch):
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_bank_ticker())

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=10")

    assert resp.status_code == 200
    fin = next(s for s in resp.json()["sectors"] if s["sector"] == "Financials")
    row = fin["stocks"][0]
    assert row["ev_to_ebitda"] is None
    assert row["fcf_yield_pct"] is None
    assert row["current_ratio"] is None
    # Score still computes from the factors that ARE available (book yield,
    # sales yield, PEG, dividend) rather than crashing or returning None outright.
    assert row["value_score"] is not None


def test_value_sectors_includes_score_breakdown_and_trend(monkeypatch):
    import pandas as pd

    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_value_ticker())
    all_syms = [s for syms in _MOMENTUM_UNIVERSE.values() for s in syms]
    # Every stock falls 20% over the window; mock price (100) sits above its
    # 200-day average (90), so the two trend signals disagree -> "mixed".
    falling = pd.DataFrame({sym: [125.0] * 100 + [100.0] * 30 for sym in all_syms})
    monkeypatch.setattr("app.main._fetch_universe_history", lambda: falling)

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    assert resp.status_code == 200
    row = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")["stocks"][0]
    assert row["score_cheapness_pts"] is not None
    assert row["score_quality_pts"] is not None
    assert row["score_penalty_pts"] == 0.0
    assert row["value_score"] == pytest.approx(
        row["score_cheapness_pts"] + row["score_quality_pts"] + row["score_penalty_pts"], abs=0.1
    )
    assert row["return_6m_pct"] == pytest.approx(-20.0)
    assert row["above_sma200"] is True
    assert row["trend_signal"] == "mixed"


def test_value_sectors_trend_falls_back_to_sma_without_history(monkeypatch):
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_value_ticker())

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    row = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")["stocks"][0]
    assert row["return_6m_pct"] is None
    assert row["trend_signal"] == "up"
