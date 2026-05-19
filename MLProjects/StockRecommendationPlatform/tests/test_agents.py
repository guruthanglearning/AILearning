"""Unit tests for all 7 specialist agents — no network calls, no DB, no Redis."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest

from app.agents.base import AgentContext
from app.agents.financials import FinancialsAgent
from app.agents.fundamentals import FundamentalsAgent
from app.agents.market_data import MarketDataAgent
from app.agents.options import OptionsAgent
from app.agents.risk_pro import RiskProWorkflowAgent
from app.agents.sentiment_ml import SentimentMLAgent
from app.agents.technicals import TechnicalsAgent
from app.providers.base import MarketDataProvider, ProviderError
from app.schemas.agents import AgentStatus


def _fake_provider() -> MagicMock:
    return MagicMock(spec=MarketDataProvider)


def _ctx(symbol: str = "AAPL", provider=None) -> AgentContext:
    return AgentContext(symbol=symbol, timeout_s=30.0, provider=provider or _fake_provider())


def _history(n: int = 70) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    prices = 100 + np.cumsum(rng.standard_normal(n) * 0.5)
    dates = pd.date_range("2025-01-01", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1, "Close": prices, "Volume": 1_000_000},
        index=dates,
    )


def _option_df(spot: float = 150.0) -> pd.DataFrame:
    strikes = [140.0, 145.0, 150.0, 155.0, 160.0]
    return pd.DataFrame(
        {
            "strike": strikes,
            "bid": [10.0, 7.0, 4.5, 2.0, 0.8],
            "ask": [10.5, 7.5, 5.0, 2.5, 1.2],
            "lastPrice": [10.2, 7.2, 4.8, 2.2, 1.0],
            "impliedVolatility": [0.35, 0.32, 0.30, 0.31, 0.34],
            "openInterest": [500, 1000, 2000, 1500, 800],
        }
    )


# ---------------------------------------------------------------------------
# MarketDataAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_market_data_agent_complete():
    prov = _fake_provider()
    prov.get_quote = AsyncMock(
        return_value={
            "last_price": 150.0,
            "previous_close": 148.0,
            "day_change_pct": 1.35,
            "volume": 50_000_000,
            "source": "yfinance",
        }
    )
    result = await MarketDataAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.last_price == 150.0


@pytest.mark.asyncio
async def test_market_data_agent_failed_when_no_price():
    prov = _fake_provider()
    prov.get_quote = AsyncMock(
        return_value={
            "last_price": None,
            "previous_close": None,
            "day_change_pct": None,
            "volume": None,
            "source": "yfinance",
        }
    )
    result = await MarketDataAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.failed
    assert result.last_price is None


@pytest.mark.asyncio
async def test_market_data_agent_failed_on_provider_error():
    prov = _fake_provider()
    prov.get_quote = AsyncMock(side_effect=ProviderError("429 rate limit"))
    result = await MarketDataAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.failed
    assert "429" in (result.error_message or "")


# ---------------------------------------------------------------------------
# FundamentalsAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fundamentals_agent_complete():
    prov = _fake_provider()
    prov.get_fundamentals = AsyncMock(
        return_value={
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "market_cap": 3_000_000_000_000.0,
            "pe_ratio": 28.5,
            "forward_pe": 26.0,
            "revenue_growth": 0.08,
            "avg_volume": 60_000_000,
            "source": "yfinance",
        }
    )
    result = await FundamentalsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.sector == "Technology"
    assert result.pe_ratio == 28.5


@pytest.mark.asyncio
async def test_fundamentals_agent_complete_with_null_fields():
    prov = _fake_provider()
    prov.get_fundamentals = AsyncMock(
        return_value={
            "company_name": None,
            "sector": None,
            "market_cap": None,
            "pe_ratio": None,
            "forward_pe": None,
            "revenue_growth": None,
            "avg_volume": None,
            "source": "yfinance",
        }
    )
    result = await FundamentalsAgent().run(_ctx(provider=prov))
    # Agent returns complete when provider doesn't raise — null fields are normal
    assert result.status == AgentStatus.complete
    assert result.sector is None


@pytest.mark.asyncio
async def test_fundamentals_agent_degraded_on_exception():
    prov = _fake_provider()
    prov.get_fundamentals = AsyncMock(side_effect=RuntimeError("network failure"))
    result = await FundamentalsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.degraded
    assert "network failure" in (result.error_message or "")


# ---------------------------------------------------------------------------
# TechnicalsAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_technicals_agent_complete():
    prov = _fake_provider()
    prov.get_price_history = AsyncMock(return_value=_history(70))
    result = await TechnicalsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.sma_20 is not None
    assert result.sma_50 is not None


@pytest.mark.asyncio
async def test_technicals_agent_degraded_when_history_too_short():
    prov = _fake_provider()
    prov.get_price_history = AsyncMock(return_value=_history(10))
    result = await TechnicalsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.degraded


@pytest.mark.asyncio
async def test_technicals_agent_trend_bullish():
    """Rising trend with small noise → SMA20 > SMA50 and RSI > 50 → bullish.

    Pure linear prices produce avg_loss=0 which makes RSI=NaN; adding noise
    ensures some down-days so RSI is computable and high in a strong uptrend.
    """
    prov = _fake_provider()
    n = 70
    rng = np.random.default_rng(7)
    prices = np.linspace(80, 150, n) + rng.standard_normal(n) * 0.5
    dates = pd.date_range("2025-01-01", periods=n, freq="B", tz="UTC")
    df = pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1, "Close": prices, "Volume": 1_000_000},
        index=dates,
    )
    prov.get_price_history = AsyncMock(return_value=df)
    result = await TechnicalsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.trend_hint == "bullish"


# ---------------------------------------------------------------------------
# FinancialsAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_financials_agent_complete_with_history():
    prov = _fake_provider()
    prov.get_price_history = AsyncMock(return_value=_history(252))
    result = await FinancialsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.filing_url_hint is not None
    assert "AAPL" in (result.filing_url_hint or "")


@pytest.mark.asyncio
async def test_financials_agent_degraded_on_empty_history():
    prov = _fake_provider()
    prov.get_price_history = AsyncMock(return_value=pd.DataFrame())
    result = await FinancialsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.degraded


@pytest.mark.asyncio
async def test_financials_agent_degraded_on_exception():
    prov = _fake_provider()
    prov.get_price_history = AsyncMock(side_effect=RuntimeError("timeout"))
    result = await FinancialsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.degraded


# ---------------------------------------------------------------------------
# OptionsAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_options_agent_complete_with_atm_iv():
    prov = _fake_provider()
    prov.get_option_chain = AsyncMock(
        return_value={
            "expiries": ["2025-06-20"],
            "chosen_expiry": "2025-06-20",
            "spot": 150.0,
            "calls": _option_df(),
            "puts": _option_df(),
            "source": "yfinance",
        }
    )
    result = await OptionsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.atm_iv is not None and result.atm_iv > 0


@pytest.mark.asyncio
async def test_options_agent_degraded_when_chain_empty():
    prov = _fake_provider()
    prov.get_option_chain = AsyncMock(
        return_value={
            "expiries": [],
            "chosen_expiry": None,
            "spot": None,
            "calls": None,
            "puts": None,
            "source": "yfinance",
        }
    )
    result = await OptionsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.degraded


@pytest.mark.asyncio
async def test_options_agent_implied_move_computed():
    prov = _fake_provider()
    prov.get_option_chain = AsyncMock(
        return_value={
            "expiries": ["2025-06-20"],
            "chosen_expiry": "2025-06-20",
            "spot": 150.0,
            "calls": _option_df(150.0),
            "puts": _option_df(150.0),
            "source": "yfinance",
        }
    )
    result = await OptionsAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.implied_move_1d_pct is not None and result.implied_move_1d_pct > 0


# ---------------------------------------------------------------------------
# RiskProWorkflowAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_riskpro_no_upcoming_earnings():
    prov = _fake_provider()
    prov.get_fundamentals = AsyncMock(
        return_value={
            "company_name": "Apple",
            "sector": "Tech",
            "market_cap": 3e12,
            "pe_ratio": 28.0,
            "forward_pe": 26.0,
            "revenue_growth": 0.08,
            "avg_volume": 60_000_000,
            "earnings_dates": None,
            "source": "yfinance",
        }
    )
    result = await RiskProWorkflowAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.has_upcoming_earnings is False


@pytest.mark.asyncio
async def test_riskpro_has_upcoming_earnings():
    prov = _fake_provider()
    soon = (pd.Timestamp.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    prov.get_fundamentals = AsyncMock(
        return_value={
            "company_name": "Apple",
            "sector": "Tech",
            "market_cap": 3e12,
            "pe_ratio": 28.0,
            "forward_pe": 26.0,
            "revenue_growth": 0.08,
            "avg_volume": 60_000_000,
            "earnings_dates": [soon],
            "source": "yfinance",
        }
    )
    result = await RiskProWorkflowAgent().run(_ctx(provider=prov))
    assert result.status == AgentStatus.complete
    assert result.has_upcoming_earnings is True
    assert result.earnings_days_away is not None and result.earnings_days_away <= 21


@pytest.mark.asyncio
async def test_riskpro_checklist_non_empty():
    prov = _fake_provider()
    prov.get_fundamentals = AsyncMock(
        return_value={
            "company_name": "Apple",
            "sector": "Tech",
            "market_cap": 3e12,
            "pe_ratio": 28.0,
            "forward_pe": 26.0,
            "revenue_growth": 0.08,
            "avg_volume": 700_000,
            "earnings_dates": None,
            "source": "yfinance",
        }
    )
    result = await RiskProWorkflowAgent().run(_ctx(provider=prov))
    assert len(result.checklist) >= 1
    ids = [item["id"] for item in result.checklist]
    assert "earnings_window" in ids


# ---------------------------------------------------------------------------
# SentimentMLAgent  (FinBERT + NewsAPI)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sentiment_agent_complete_with_finbert(monkeypatch):
    monkeypatch.setattr("app.agents.sentiment_ml.settings.news_api_key", "test-key")
    monkeypatch.setattr("app.agents.sentiment_ml._HF_AVAILABLE", True)

    monkeypatch.setattr(
        "app.agents.sentiment_ml._fetch_articles_sync",
        lambda symbol, key: ["Apple beats earnings estimates", "AAPL hits all-time high"],
    )
    monkeypatch.setattr(
        "app.agents.sentiment_ml._score_headlines",
        lambda pipe, headlines: (0.72, ["Apple beats earnings estimates"]),
    )

    async def _mock_pipeline():
        return MagicMock()

    monkeypatch.setattr("app.agents.sentiment_ml._get_pipeline", _mock_pipeline)

    result = await SentimentMLAgent().run(_ctx())
    assert result.status == AgentStatus.complete
    assert result.sentiment_score == pytest.approx(0.72)
    assert result.forecast_signal == "Bullish"
    assert len(result.top_headlines) == 1


@pytest.mark.asyncio
async def test_sentiment_agent_degraded_when_no_api_key(monkeypatch):
    monkeypatch.setattr("app.agents.sentiment_ml.settings.news_api_key", None)
    result = await SentimentMLAgent().run(_ctx())
    assert result.status == AgentStatus.degraded
    assert "NEWS_API_KEY" in (result.confidence_note or "")


@pytest.mark.asyncio
async def test_sentiment_agent_degraded_on_newsapi_error(monkeypatch):
    def _raise(symbol, key):
        raise RuntimeError("rate limited")

    monkeypatch.setattr("app.agents.sentiment_ml.settings.news_api_key", "test-key")
    monkeypatch.setattr("app.agents.sentiment_ml._HF_AVAILABLE", True)
    monkeypatch.setattr("app.agents.sentiment_ml._fetch_articles_sync", _raise)

    result = await SentimentMLAgent().run(_ctx())
    assert result.status == AgentStatus.degraded


@pytest.mark.asyncio
async def test_sentiment_agent_degraded_hf_unavailable(monkeypatch):
    monkeypatch.setattr("app.agents.sentiment_ml.settings.news_api_key", "test-key")
    monkeypatch.setattr("app.agents.sentiment_ml._HF_AVAILABLE", False)
    result = await SentimentMLAgent().run(_ctx())
    assert result.status == AgentStatus.degraded
    assert "transformers" in (result.confidence_note or "").lower()


@pytest.mark.asyncio
async def test_sentiment_agent_degraded_no_headlines(monkeypatch):
    monkeypatch.setattr("app.agents.sentiment_ml.settings.news_api_key", "test-key")
    monkeypatch.setattr("app.agents.sentiment_ml._HF_AVAILABLE", True)
    monkeypatch.setattr("app.agents.sentiment_ml._fetch_articles_sync", lambda s, k: [])
    result = await SentimentMLAgent().run(_ctx())
    assert result.status == AgentStatus.degraded
    assert "No recent news" in (result.confidence_note or "")


@pytest.mark.asyncio
async def test_sentiment_agent_degraded_on_finbert_failure(monkeypatch):
    monkeypatch.setattr("app.agents.sentiment_ml.settings.news_api_key", "test-key")
    monkeypatch.setattr("app.agents.sentiment_ml._HF_AVAILABLE", True)
    monkeypatch.setattr(
        "app.agents.sentiment_ml._fetch_articles_sync",
        lambda s, k: ["Some headline"],
    )

    async def _failing_pipeline():
        raise RuntimeError("model load failed")

    monkeypatch.setattr("app.agents.sentiment_ml._get_pipeline", _failing_pipeline)
    result = await SentimentMLAgent().run(_ctx())
    assert result.status == AgentStatus.degraded


# _to_signal and _score_headlines direct unit tests

def test_to_signal_bullish():
    from app.agents.sentiment_ml import _to_signal
    assert _to_signal(0.5) == "Bullish"


def test_to_signal_bearish():
    from app.agents.sentiment_ml import _to_signal
    assert _to_signal(-0.5) == "Bearish"


def test_to_signal_neutral():
    from app.agents.sentiment_ml import _to_signal
    assert _to_signal(0.0) == "Neutral"


def test_score_headlines_aggregation():
    from app.agents.sentiment_ml import _score_headlines
    mock_pipe = MagicMock()
    mock_pipe.return_value = [
        {"label": "positive", "score": 0.8},
        {"label": "negative", "score": 0.1},
        {"label": "neutral", "score": 0.1},
    ]
    score, top = _score_headlines(mock_pipe, ["AAPL beats earnings"])
    assert score == pytest.approx(0.7, abs=0.01)
    assert top == ["AAPL beats earnings"]


def test_score_headlines_empty():
    from app.agents.sentiment_ml import _score_headlines
    score, top = _score_headlines(MagicMock(), [])
    assert score == 0.0
    assert top == []
