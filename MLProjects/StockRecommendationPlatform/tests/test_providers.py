"""Provider layer tests — no live network calls, no Postgres, no Redis required."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from app.providers.base import MarketDataProvider
from app.providers.factory import build_provider
from app.providers.yfinance_provider import YFinanceProvider


# ---------------------------------------------------------------------------
# Factory selection
# ---------------------------------------------------------------------------


def test_factory_returns_yfinance_when_no_key(monkeypatch):
    monkeypatch.setattr("app.providers.factory.settings.polygon_api_key", None)
    monkeypatch.setattr("app.providers.factory.settings.use_redis", False)
    p = build_provider()
    assert isinstance(p, YFinanceProvider)


def test_factory_returns_redis_cache_when_use_redis(monkeypatch):
    from app.providers.redis_cache import RedisCache

    monkeypatch.setattr("app.providers.factory.settings.polygon_api_key", None)
    monkeypatch.setattr("app.providers.factory.settings.use_redis", True)
    monkeypatch.setattr("app.providers.factory.settings.redis_url", "redis://localhost:6380/0")
    p = build_provider()
    assert isinstance(p, RedisCache)
    assert isinstance(p._inner, YFinanceProvider)


def test_factory_returns_polygon_when_key_set(monkeypatch):
    from app.providers.polygon_provider import PolygonProvider

    monkeypatch.setattr("app.providers.factory.settings.polygon_api_key", "pk_test_key")
    monkeypatch.setattr("app.providers.factory.settings.use_redis", False)
    p = build_provider()
    assert isinstance(p, PolygonProvider)


def test_factory_returns_redis_wrapping_polygon_when_both_set(monkeypatch):
    from app.providers.polygon_provider import PolygonProvider
    from app.providers.redis_cache import RedisCache

    monkeypatch.setattr("app.providers.factory.settings.polygon_api_key", "pk_test_key")
    monkeypatch.setattr("app.providers.factory.settings.use_redis", True)
    monkeypatch.setattr("app.providers.factory.settings.redis_url", "redis://localhost:6380/0")
    p = build_provider()
    assert isinstance(p, RedisCache)
    assert isinstance(p._inner, PolygonProvider)


# ---------------------------------------------------------------------------
# YFinanceProvider: structure of returned dicts
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_history() -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=70, freq="B", tz="UTC")
    import numpy as np

    prices = 100 + np.cumsum(np.random.randn(70) * 0.5)
    return pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1, "Close": prices, "Volume": 1_000_000},
        index=dates,
    )


@pytest.mark.asyncio
async def test_yfinance_provider_get_quote_structure(monkeypatch, fake_history):
    provider = YFinanceProvider()
    monkeypatch.setattr(
        "app.providers.yfinance_provider.YFinanceProvider.get_quote",
        AsyncMock(
            return_value={
                "last_price": 150.0,
                "previous_close": 148.0,
                "day_change_pct": 1.35,
                "volume": 50_000_000,
                "source": "yfinance",
            }
        ),
    )
    q = await provider.get_quote("AAPL")
    assert isinstance(q["last_price"], float)
    assert q["source"] == "yfinance"


@pytest.mark.asyncio
async def test_yfinance_provider_get_price_history_structure(monkeypatch, fake_history):
    provider = YFinanceProvider()
    monkeypatch.setattr(
        "app.providers.yfinance_provider.YFinanceProvider.get_price_history",
        AsyncMock(return_value=fake_history),
    )
    df = await provider.get_price_history("AAPL", "6mo")
    assert not df.empty
    assert "Close" in df.columns
    assert len(df) >= 50


# ---------------------------------------------------------------------------
# RedisCache: cache-hit path avoids inner provider call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_cache_hit_skips_inner_provider(monkeypatch):
    from app.providers.redis_cache import RedisCache

    inner = AsyncMock(spec=MarketDataProvider)
    cached_quote = {
        "last_price": 200.0,
        "previous_close": 198.0,
        "day_change_pct": 1.0,
        "volume": 1_000_000,
        "source": "yfinance",
    }

    cache = RedisCache(inner=inner, redis_url="redis://localhost:6380/0")
    # Simulate cache hit
    cache._get = AsyncMock(return_value=cached_quote)
    cache._set = AsyncMock()

    result = await cache.get_quote("AAPL")
    assert result == cached_quote
    inner.get_quote.assert_not_called()


@pytest.mark.asyncio
async def test_redis_cache_miss_calls_inner_and_stores(monkeypatch):
    from app.providers.redis_cache import RedisCache

    fetched = {
        "last_price": 300.0,
        "previous_close": 295.0,
        "day_change_pct": 1.7,
        "volume": 2_000_000,
        "source": "yfinance",
    }
    inner = AsyncMock(spec=MarketDataProvider)
    inner.get_quote = AsyncMock(return_value=fetched)

    cache = RedisCache(inner=inner, redis_url="redis://localhost:6380/0")
    cache._get = AsyncMock(return_value=None)  # cache miss
    cache._set = AsyncMock()

    result = await cache.get_quote("MSFT")
    assert result == fetched
    inner.get_quote.assert_awaited_once_with("MSFT")
    cache._set.assert_awaited_once()
