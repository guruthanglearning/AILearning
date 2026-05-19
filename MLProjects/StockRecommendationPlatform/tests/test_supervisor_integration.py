"""End-to-end supervisor integration tests — fully mocked provider, no DB, no network."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest

from app.providers.base import MarketDataProvider
from app.schemas.agents import AnalysisRunRequest, InstrumentRecommendation
from app.supervisor import Supervisor


def _history(n: int = 70) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    prices = 100 + np.cumsum(rng.standard_normal(n) * 0.5)
    dates = pd.date_range("2025-01-01", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1, "Close": prices, "Volume": 1_000_000},
        index=dates,
    )


def _option_df() -> pd.DataFrame:
    strikes = [140.0, 145.0, 150.0, 155.0, 160.0]
    return pd.DataFrame(
        {
            "strike": strikes,
            "bid": [10.0, 7.0, 4.5, 2.0, 0.8],
            "ask": [10.5, 7.5, 5.0, 2.5, 1.2],
            "lastPrice": [10.2, 7.2, 4.8, 2.2, 1.0],
            "impliedVolatility": [0.25, 0.23, 0.22, 0.23, 0.25],
            "openInterest": [800, 1200, 2500, 1800, 900],
        }
    )


def _iv_rich_option_df() -> pd.DataFrame:
    strikes = [140.0, 145.0, 150.0, 155.0, 160.0]
    return pd.DataFrame(
        {
            "strike": strikes,
            "bid": [18.0, 14.0, 10.0, 6.0, 3.0],
            "ask": [19.0, 15.0, 11.0, 7.0, 4.0],
            "lastPrice": [18.5, 14.5, 10.5, 6.5, 3.5],
            "impliedVolatility": [0.55, 0.52, 0.50, 0.51, 0.53],
            "openInterest": [800, 1200, 2500, 1800, 900],
        }
    )


def _build_mock_provider(
    last_price: float = 150.0,
    atm_iv: float = 0.22,
    earnings_dates=None,
    option_df_fn=None,
) -> MagicMock:
    prov = MagicMock(spec=MarketDataProvider)
    prov.get_quote = AsyncMock(
        return_value={
            "last_price": last_price,
            "previous_close": last_price - 2,
            "day_change_pct": 1.0,
            "volume": 60_000_000,
            "source": "mock",
        }
    )
    prov.get_fundamentals = AsyncMock(
        return_value={
            "company_name": "Test Corp",
            "sector": "Technology",
            "market_cap": 2e12,
            "pe_ratio": 25.0,
            "forward_pe": 22.0,
            "revenue_growth": 0.10,
            "avg_volume": 50_000_000,
            "earnings_dates": earnings_dates,
            "source": "mock",
        }
    )
    prov.get_price_history = AsyncMock(return_value=_history(70))
    opt_df = option_df_fn() if option_df_fn else _option_df()
    prov.get_option_chain = AsyncMock(
        return_value={
            "expiries": ["2025-06-20"],
            "chosen_expiry": "2025-06-20",
            "spot": last_price,
            "calls": opt_df,
            "puts": opt_df,
            "source": "mock",
        }
    )
    return prov


async def _mock_get_session_gen():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    yield session


def _mock_session_factory():
    return _mock_get_session_gen()


def _req(symbol: str = "AAPL") -> AnalysisRunRequest:
    return AnalysisRunRequest(symbol=symbol)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_analysis_bullish_market_data(monkeypatch):
    """Rising prices + adequate IV → stock or options recommendation."""
    prov = _build_mock_provider(last_price=150.0)
    monkeypatch.setattr("app.supervisor.build_provider", lambda: prov)
    monkeypatch.setattr("app.supervisor.get_session", _mock_session_factory)
    monkeypatch.setattr("app.agents.sentiment_ml.settings.finnhub_api_key", None)

    verdict = await Supervisor().run_analysis(_req())
    assert verdict.instrument_recommendation in (
        InstrumentRecommendation.stock,
        InstrumentRecommendation.options,
    )
    assert len(verdict.agent_contributions) == 7
    assert verdict.decision_aids is not None


@pytest.mark.asyncio
async def test_full_analysis_failed_market_data(monkeypatch):
    """When market data agent fails, supervisor returns insufficient_data."""

    prov = _build_mock_provider()
    prov.get_quote = AsyncMock(side_effect=Exception("provider down"))
    monkeypatch.setattr("app.supervisor.build_provider", lambda: prov)
    monkeypatch.setattr("app.supervisor.get_session", _mock_session_factory)
    monkeypatch.setattr("app.agents.sentiment_ml.settings.finnhub_api_key", None)

    verdict = await Supervisor().run_analysis(_req())
    assert verdict.instrument_recommendation == InstrumentRecommendation.insufficient_data


@pytest.mark.asyncio
async def test_full_analysis_earnings_imminent(monkeypatch):
    """Earnings within 3 weeks + mixed technicals → options recommendation."""
    from datetime import timedelta

    soon = (pd.Timestamp.today() + timedelta(days=7)).strftime("%Y-%m-%d")
    prov = _build_mock_provider(last_price=150.0, earnings_dates=[soon])

    # Use flat prices to get "mixed" trend (SMA20 ≈ SMA50)
    flat = pd.DataFrame(
        {"Open": [150.0] * 70, "High": [151.0] * 70, "Low": [149.0] * 70,
         "Close": [150.0] * 70, "Volume": [1_000_000] * 70},
        index=pd.date_range("2025-01-01", periods=70, freq="B", tz="UTC"),
    )
    prov.get_price_history = AsyncMock(return_value=flat)

    monkeypatch.setattr("app.supervisor.build_provider", lambda: prov)
    monkeypatch.setattr("app.supervisor.get_session", _mock_session_factory)
    monkeypatch.setattr("app.agents.sentiment_ml.settings.finnhub_api_key", None)

    verdict = await Supervisor().run_analysis(_req())
    assert verdict.instrument_recommendation == InstrumentRecommendation.options
    assert "earnings" in verdict.confidence_note.lower()


@pytest.mark.asyncio
async def test_full_analysis_high_iv(monkeypatch):
    """IV > 0.35 + no imminent earnings → options (premium selling) recommendation."""
    prov = _build_mock_provider(last_price=150.0, option_df_fn=_iv_rich_option_df)
    monkeypatch.setattr("app.supervisor.build_provider", lambda: prov)
    monkeypatch.setattr("app.supervisor.get_session", _mock_session_factory)
    monkeypatch.setattr("app.agents.sentiment_ml.settings.finnhub_api_key", None)

    verdict = await Supervisor().run_analysis(_req())
    assert verdict.instrument_recommendation == InstrumentRecommendation.options


@pytest.mark.asyncio
async def test_full_analysis_agent_timeout_handled(monkeypatch):
    """safe_run converts TimeoutError into a failed agent result; supervisor still completes."""
    import asyncio

    prov = _build_mock_provider(last_price=150.0)
    # Make options agent time out

    async def _slow(*_a, **_kw):
        await asyncio.sleep(100)

    prov.get_option_chain = AsyncMock(side_effect=_slow)
    monkeypatch.setattr("app.supervisor.build_provider", lambda: prov)
    monkeypatch.setattr("app.supervisor.get_session", _mock_session_factory)
    monkeypatch.setattr("app.agents.sentiment_ml.settings.finnhub_api_key", None)
    # Use a very short timeout so the test doesn't actually sleep 100s
    monkeypatch.setattr("app.supervisor.settings.agent_timeout_seconds", 0.05)

    verdict = await Supervisor().run_analysis(_req())
    # Supervisor must still return a valid verdict
    assert verdict.instrument_recommendation in InstrumentRecommendation.__members__.values()
    # The options agent contribution should show failed/timeout
    opt_contrib = next(
        (c for c in verdict.agent_contributions if c.agent_name == "OptionsAgent"), None
    )
    assert opt_contrib is not None
    assert opt_contrib.status.value in ("failed", "degraded")
