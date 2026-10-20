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
    _fetch_statements,
    _fetch_stock_raw,
    _gather_statements,
    _graham_number_and_margin,
    _percentile_ranks,
    _percentile_ranks_by_group,
    _piotroski_fscore,
    _value_score_breakdown,
    _value_trend_signal,
    _vs,
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
    # Graham's margin of safety is measured against intrinsic value, not price.
    assert margin == pytest.approx((expected_graham - 80.0) / expected_graham * 100.0, abs=0.1)


def test_graham_margin_uses_intrinsic_value_as_denominator():
    # EPS 5, BVPS 80 -> Graham Number sqrt(22.5*5*80) = 94.87; at price 47.43 the
    # price is ~50% below value. Dividing by price instead would report ~100%.
    graham, margin = _graham_number_and_margin(trailing_eps=5.0, book_value_per_share=80.0, price=47.43)
    assert graham == pytest.approx(94.87, abs=0.01)
    assert margin == pytest.approx(50.0, abs=0.1)


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
    # Levered FCF over market cap (2.5B / 50B), not over enterprise value.
    assert row["fcf_yield_pct"] == pytest.approx(5.0)
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


@pytest.mark.parametrize("market_cap", [None, 0, -50_000_000_000])
def test_value_sectors_fcf_yield_none_without_positive_market_cap(monkeypatch, market_cap):
    # Negative FCF over a non-positive denominator must never become a positive yield.
    monkeypatch.setattr(
        "app.main.yf.Ticker",
        lambda sym: _mock_value_ticker(freeCashflow=-10_000_000, marketCap=market_cap),
    )

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    assert resp.status_code == 200
    row = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")["stocks"][0]
    assert row["fcf_yield_pct"] is None


# ---------------------------------------------------------------------------
# Piotroski F-score
# ---------------------------------------------------------------------------


def _acme_statements(**overrides) -> dict:
    """Most recent year first (three balance sheets, as the ROA, turnover and
    leverage tests need): profitable, cash-backed, de-levering, more liquid,
    better margins and turnover, but sold new stock -> 8/9."""
    st = {
        "fiscal_year_end": "2025-12-31",
        "net_income": [100e6, 80e6, 70e6],
        "revenue": [900e6, 800e6, 750e6],
        "gross_profit": [360e6, 304e6, 280e6],
        "total_assets": [1000e6, 1000e6, 1000e6],
        "long_term_debt": [250e6, 300e6, 320e6],
        "current_assets": [160e6, 140e6, 130e6],
        "current_liabilities": [100e6, 100e6, 100e6],
        "operating_cash_flow": [130e6, 90e6, 80e6],
        "stock_issuance": [5e6, None, None],
        "net_stock_issuance": [5e6, -10e6, -10e6],
    }
    st.update(overrides)
    return st


def _bank_statements() -> dict:
    # Unclassified balance sheet (no current assets/liabilities), no gross profit,
    # negative operating cash flow from lending, as in real JPM-style data.
    return _acme_statements(
        gross_profit=[None, None],
        current_assets=[None, None],
        current_liabilities=[None, None],
        operating_cash_flow=[-150e9, -40e9],
        stock_issuance=[None, None],
        net_stock_issuance=[-2e9, -1e9],
    )


def test_piotroski_acme_example_scores_8_of_9():
    f = _piotroski_fscore(_acme_statements())
    assert f["score"] == 8
    assert f["max"] == 9
    assert f["bank_style"] is False
    assert f["fiscal_year"] == "2025-12-31"
    assert [t["id"] for t in f["tests"] if t["passed"] is False] == ["no_dilution"]
    details = {t["id"]: t["detail"] for t in f["tests"]}
    assert details["roa_up"] == "ROA 10.0% vs 8.0%"
    assert details["leverage_down"] == "Long-term debt (share of average assets) 25.0% vs 30.0%"
    assert details["no_dilution"] == "Issued $5M of new common stock"
    assert details["gross_margin_up"] == "40.0% vs 38.0%"


def test_piotroski_none_without_statements():
    assert _piotroski_fscore(None) is None
    assert _piotroski_fscore({}) is None


def test_piotroski_missing_data_is_not_evaluated_rather_than_failed():
    f = _piotroski_fscore(_acme_statements(current_assets=[None, None]))
    current = next(t for t in f["tests"] if t["id"] == "current_ratio_up")
    assert current["passed"] is None
    assert current["detail"] == "Data not reported"
    assert f["max"] == 8
    assert f["score"] == 7


def test_piotroski_bank_style_skips_tests_that_dont_apply():
    f = _piotroski_fscore(_bank_statements(), financial_sector=True, industry="Banks - Diversified")
    assert f["bank_style"] is True
    skipped = {t["id"] for t in f["tests"] if t["passed"] is None}
    assert skipped == {"cfo", "accruals", "leverage_down", "current_ratio_up", "gross_margin_up"}
    assert all(
        t["detail"].startswith("Not meaningful for banks")
        for t in f["tests"] if t["passed"] is None
    )
    assert f["max"] == 4
    assert f["score"] == 4


def test_piotroski_bank_style_skips_gross_margin_even_when_reported():
    st = _bank_statements()
    st["gross_profit"] = [50e9, 40e9]
    f = _piotroski_fscore(st, financial_sector=True, industry="Insurance - Diversified")
    gm = next(t for t in f["tests"] if t["id"] == "gross_margin_up")
    assert gm["passed"] is None
    assert gm["detail"] == "Not meaningful for banks/insurers: no cost of goods sold"
    assert f["max"] == 4


def test_piotroski_unclassified_balance_sheet_outside_financials_is_not_bank_style():
    # Same statements, but not a Financials-sector company: the cash-flow tests
    # still apply, and the negative cash flow fails them.
    f = _piotroski_fscore(_bank_statements(), financial_sector=False, industry="Banks - Diversified")
    assert f["bank_style"] is False
    cfo = next(t for t in f["tests"] if t["id"] == "cfo")
    assert cfo["passed"] is False


def test_piotroski_financial_with_classified_balance_sheet_gets_all_nine_tests():
    # e.g. an asset manager: Financials sector, but a normal balance sheet.
    f = _piotroski_fscore(_acme_statements(), financial_sector=True, industry="Credit Services")
    assert f["bank_style"] is False
    assert f["max"] == 9


def test_piotroski_non_bank_financial_with_missing_current_assets_is_not_bank_style():
    # An asset manager with a gap in Yahoo's current-assets data: the gap is just
    # missing data, so the cash-flow tests still run (and negative cash flow fails).
    st = _acme_statements(current_assets=[None, None, None], operating_cash_flow=[-5e6, 90e6, 80e6])
    f = _piotroski_fscore(st, financial_sector=True, industry="Asset Management")
    assert f["bank_style"] is False
    tests = {t["id"]: t for t in f["tests"]}
    assert tests["cfo"]["passed"] is False
    assert tests["current_ratio_up"]["detail"] == "Data not reported"


def test_piotroski_bank_style_needs_both_years_without_current_assets():
    st = _bank_statements()
    st["current_assets"] = [None, 140e6]
    f = _piotroski_fscore(st, financial_sector=True, industry="Banks - Regional")
    assert f["bank_style"] is False


def test_piotroski_no_score_when_too_few_tests_evaluable():
    sparse = {"fiscal_year_end": "2025-12-31", "net_income": [5e6, 4e6], "net_stock_issuance": [-1e6, 0.0]}
    f = _piotroski_fscore(sparse)
    assert f["max"] == 2
    assert f["score"] is None


def test_piotroski_roa_uses_beginning_of_year_assets_when_available():
    # Three balance sheets: ROA for year t = net income t / assets at the end of year t-1.
    f = _piotroski_fscore(_acme_statements(total_assets=[1000e6, 500e6, 1000e6]))
    roa = next(t for t in f["tests"] if t["id"] == "roa_up")
    assert roa["detail"] == "ROA 20.0% vs 8.0%"
    assert roa["passed"] is True


def test_piotroski_asset_based_tests_not_evaluated_without_third_balance_sheet():
    # Income 80 -> 100 while assets double: year-end ROA would read 5.0% vs 8.0% (a
    # fail) although beginning-of-year ROA rose to 10.0%, so without the third
    # balance sheet these tests are skipped rather than computed on another base.
    st = _acme_statements(total_assets=[2000e6, 1000e6])
    f = _piotroski_fscore(st)
    tests = {t["id"]: t for t in f["tests"]}
    for test_id in ("roa_up", "leverage_down", "asset_turnover_up"):
        assert tests[test_id]["passed"] is None
        assert tests[test_id]["detail"] == "Needs three years of balance sheets"
    assert f["max"] == 6


def test_piotroski_issuance_with_larger_buybacks_still_fails():
    # Sold $50M of new stock but bought back $200M: share count fell, yet equity
    # was issued, so the test fails.
    f = _piotroski_fscore(_acme_statements(stock_issuance=[50e6, None], net_stock_issuance=[-150e6, 0.0]))
    test = next(t for t in f["tests"] if t["id"] == "no_dilution")
    assert test["passed"] is False
    assert test["detail"] == "Issued $50M of new common stock"


def test_piotroski_no_issuance_row_with_buybacks_passes():
    f = _piotroski_fscore(_acme_statements(stock_issuance=[None], net_stock_issuance=[-90e9]))
    test = next(t for t in f["tests"] if t["id"] == "no_dilution")
    assert test["passed"] is True
    assert test["detail"] == "No issuance reported (net buybacks $90.0B)"


def test_piotroski_issuance_not_evaluated_without_financing_data():
    f = _piotroski_fscore(_acme_statements(stock_issuance=[None], net_stock_issuance=[None]))
    test = next(t for t in f["tests"] if t["id"] == "no_dilution")
    assert test["passed"] is None
    assert f["max"] == 8


def test_vs_adds_decimals_until_values_differ():
    def pct(v, d):
        return f"{v * 100:.{d}f}%"

    assert _vs(0.0154, 0.0149, pct) == "1.54% vs 1.49%"
    assert _vs(0.10, 0.08, pct) == "10.0% vs 8.0%"
    assert _vs(0.5, 0.5, pct) == "50.0000% vs 50.0000%"


def test_fetch_statements_aligns_years_most_recent_first(monkeypatch):
    import pandas as pd

    y25, y24, y23, y22 = (pd.Timestamp(f"{y}-12-31") for y in (2025, 2024, 2023, 2022))
    # Income statement has an extra older year; balance sheet columns come oldest-first.
    inc = pd.DataFrame(
        {y25: [100.0, 900.0], y24: [80.0, 800.0], y23: [70.0, 700.0], y22: [60.0, 600.0]},
        index=["Net Income", "Total Revenue"],
    )
    bs = pd.DataFrame(
        {y23: [900.0, float("nan")], y24: [950.0, 40.0], y25: [1000.0, 45.0]},
        index=["Total Assets", "Long Term Debt"],
    )
    cf = pd.DataFrame(
        {y25: [130.0, -20.0], y24: [90.0, float("nan")]},
        index=["Operating Cash Flow", "Net Common Stock Issuance"],
    )
    ticker = MagicMock()
    ticker.income_stmt, ticker.balance_sheet, ticker.cashflow = inc, bs, cf
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    st = _fetch_statements("AAA")
    assert st["fiscal_year_end"] == "2025-12-31"
    assert st["net_income"] == [100.0, 80.0, 70.0]
    assert st["total_assets"] == [1000.0, 950.0, 900.0]
    assert st["long_term_debt"] == [45.0, 40.0, None]
    assert st["operating_cash_flow"] == [130.0, 90.0, None]
    assert st["net_stock_issuance"] == [-20.0, None, None]
    assert st["stock_issuance"] == [None, None, None]
    assert st["gross_profit"] == [None, None, None]


def test_fetch_statements_stops_at_a_missing_fiscal_year(monkeypatch):
    import pandas as pd

    y25, y24, y22 = (pd.Timestamp(f"{y}-12-31") for y in (2025, 2024, 2022))
    # 2023 is missing: only 2025 and 2024 are consecutive, so 2022 must not be
    # used as 2024's prior year.
    inc = pd.DataFrame({y25: [100.0], y24: [80.0], y22: [60.0]}, index=["Net Income"])
    bs = pd.DataFrame({y25: [1000.0], y24: [950.0], y22: [900.0]}, index=["Total Assets"])
    ticker = MagicMock()
    ticker.income_stmt, ticker.balance_sheet, ticker.cashflow = inc, bs, pd.DataFrame()
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    st = _fetch_statements("AAA")
    assert st["net_income"] == [100.0, 80.0]
    assert st["total_assets"] == [1000.0, 950.0]

    # A gap right after the latest year leaves no consecutive pair at all.
    inc2 = pd.DataFrame({y25: [100.0], y22: [60.0]}, index=["Net Income"])
    bs2 = pd.DataFrame({y25: [1000.0], y22: [900.0]}, index=["Total Assets"])
    ticker.income_stmt, ticker.balance_sheet = inc2, bs2
    assert _fetch_statements("AAA") is None


def test_fetch_statements_none_without_two_shared_years(monkeypatch):
    import pandas as pd

    ticker = MagicMock()
    ticker.income_stmt = pd.DataFrame({pd.Timestamp("2025-12-31"): [1.0]}, index=["Net Income"])
    ticker.balance_sheet = pd.DataFrame({pd.Timestamp("2025-12-31"): [1.0]}, index=["Total Assets"])
    ticker.cashflow = pd.DataFrame()
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)
    assert _fetch_statements("AAA") is None

    # A ticker whose statements are not DataFrames at all, like the .info-only mocks.
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: MagicMock())
    assert _fetch_statements("AAA") is None


def test_gather_statements_caches_hits_and_misses(monkeypatch):
    import asyncio

    calls: list[str] = []

    def _fake(sym):
        calls.append(sym)
        return _acme_statements() if sym == "AAA" else None

    monkeypatch.setattr("app.main._fetch_statements", _fake)
    asyncio.run(_gather_statements(["AAA", "BBB"]))
    second = asyncio.run(_gather_statements(["AAA", "BBB"]))
    # The miss is cached too (retried after an hour), so neither symbol re-fetches.
    assert sorted(calls) == ["AAA", "BBB"]
    assert second[0]["net_income"] == [100e6, 80e6, 70e6]
    assert second[1] is None


def test_gather_statements_retries_a_miss_after_its_ttl(monkeypatch):
    import asyncio

    from app import main as main_module

    calls: list[str] = []
    monkeypatch.setattr("app.main._fetch_statements", lambda sym: calls.append(sym))
    asyncio.run(_gather_statements(["BBB"]))
    stamp, value = main_module._TTL_CACHE["value_statements_miss:BBB"]
    main_module._TTL_CACHE["value_statements_miss:BBB"] = (
        stamp - main_module._STATEMENT_MISS_TTL_SECS - 1, value,
    )
    asyncio.run(_gather_statements(["BBB"]))
    assert calls == ["BBB", "BBB"]


def test_value_sectors_includes_piotroski_fscore(monkeypatch):
    financials = set(_MOMENTUM_UNIVERSE["Financials"])
    monkeypatch.setattr(
        "app.main.yf.Ticker",
        lambda sym: _mock_value_ticker(industry="Banks - Diversified")
        if sym in financials else _mock_value_ticker(),
    )
    monkeypatch.setattr(
        "app.main._fetch_statements",
        lambda sym: _bank_statements() if sym in financials else _acme_statements(),
    )

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    assert resp.status_code == 200
    sectors = {s["sector"]: s for s in resp.json()["sectors"]}
    tech = sectors["Technology"]["stocks"][0]
    assert tech["piotroski_score"] == 8
    assert tech["piotroski_max"] == 9
    assert tech["piotroski_bank_style"] is False
    assert tech["piotroski_fiscal_year"] == "2025-12-31"
    assert len(tech["piotroski_tests"]) == 9
    bank = sectors["Financials"]["stocks"][0]
    assert bank["piotroski_bank_style"] is True
    assert bank["piotroski_max"] == 4


def test_value_sectors_piotroski_none_without_statements(monkeypatch):
    # The .info-only ticker mock has no statement DataFrames.
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_value_ticker())

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=5")

    row = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")["stocks"][0]
    assert row["piotroski_score"] is None
    assert row["piotroski_tests"] == []
    # The value score itself is unaffected.
    assert row["value_score"] is not None
