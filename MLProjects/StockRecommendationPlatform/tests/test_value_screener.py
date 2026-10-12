"""Tests for the value screener: _compute_value_score_pro scoring and /v1/value/sectors."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from app.limiter import limiter
from app.main import _MOMENTUM_UNIVERSE, _SECTOR_ETFS, _compute_value_score_pro, app


@pytest.fixture(autouse=True)
def _patch_lifespan_deps(monkeypatch):
    monkeypatch.setattr("app.db.session.init_engine", lambda: None)
    monkeypatch.setattr("app.observability.configure_otel", lambda: None)
    monkeypatch.setattr("app.main.configure_otel", lambda: None)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


# ---------------------------------------------------------------------------
# _compute_value_score_pro — pure scoring function
# ---------------------------------------------------------------------------


def test_value_score_none_when_no_percentiles_available():
    score = _compute_value_score_pro(None, None, None, None, None, None, None)
    assert score is None


def test_value_score_cheap_and_high_quality_scores_high():
    score = _compute_value_score_pro(
        pct_earnings_yield=90.0,
        pct_book_yield=90.0,
        pct_fcf_yield=90.0,
        pct_peg_inv=90.0,
        pct_dividend=90.0,
        return_on_equity_pct=20.0,   # > 15% → +8
        debt_to_equity_pct=30.0,     # < 50% → +7
    )
    assert score is not None
    assert score == pytest.approx(0.90 * 0.85 * 100 + 15.0, abs=0.2)
    assert score <= 100.0


def test_value_score_expensive_and_weak_quality_scores_low():
    score = _compute_value_score_pro(
        pct_earnings_yield=5.0,
        pct_book_yield=5.0,
        pct_fcf_yield=5.0,
        pct_peg_inv=5.0,
        pct_dividend=5.0,
        return_on_equity_pct=-2.0,   # unprofitable → no bonus
        debt_to_equity_pct=250.0,    # overleveraged → no bonus + penalty
    )
    assert score is not None
    assert score < 10.0  # cheapness pool near 0 and penalty applied
    assert score >= 0.0  # clamped, never negative


def test_value_score_overleverage_penalty_reduces_score():
    base_kwargs = dict(
        pct_earnings_yield=50.0,
        pct_book_yield=50.0,
        pct_fcf_yield=50.0,
        pct_peg_inv=50.0,
        pct_dividend=50.0,
        return_on_equity_pct=10.0,
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
        pct_peg_inv=None,
        pct_dividend=None,
        return_on_equity_pct=None,
        debt_to_equity_pct=None,
    )
    assert score is not None
    assert score == pytest.approx(85.0, abs=0.2)


def test_value_score_clamped_to_100():
    score = _compute_value_score_pro(
        pct_earnings_yield=100.0,
        pct_book_yield=100.0,
        pct_fcf_yield=100.0,
        pct_peg_inv=100.0,
        pct_dividend=100.0,
        return_on_equity_pct=50.0,
        debt_to_equity_pct=0.0,
    )
    assert score == 100.0


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
        "pegRatio": 1.2,
        "dividendYield": 1.8,
        "debtToEquity": 40.0,
        "returnOnEquity": 0.18,
        "freeCashflow": 2_500_000_000,
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
    assert row["dividend_yield_pct"] == 1.8
    assert row["debt_to_equity_pct"] == 40.0


def test_value_sectors_rows_sorted_by_score_descending(monkeypatch):
    # Give every symbol identical fundamentals except PE so scores differ deterministically.
    def _ticker(sym: str) -> MagicMock:
        pe = 10.0 if sym in ("AAPL", "MSFT") else 40.0
        return _mock_value_ticker(trailingPE=pe)

    monkeypatch.setattr("app.main.yf.Ticker", _ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/value/sectors?limit=10")

    assert resp.status_code == 200
    tech = next(s for s in resp.json()["sectors"] if s["sector"] == "Technology")
    scores = [r["value_score"] for r in tech["stocks"] if r["value_score"] is not None]
    assert scores == sorted(scores, reverse=True)
    # The two cheap-PE stocks should clearly outrank the rest of the sector.
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
