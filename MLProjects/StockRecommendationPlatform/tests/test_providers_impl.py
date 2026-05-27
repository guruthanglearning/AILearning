"""
Real-implementation tests for YFinanceProvider, PolygonProvider, and RedisCache.
No live network calls — all external I/O is mocked at the library level.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import httpx
import pandas as pd
import pytest

from app.providers.base import ProviderError
from app.providers.polygon_provider import PolygonProvider
from app.providers.yfinance_provider import YFinanceProvider

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _hist_df(n: int = 10) -> pd.DataFrame:
    import numpy as np
    dates = pd.date_range("2025-01-01", periods=n, freq="B", tz="UTC")
    prices = 100.0 + np.arange(n, dtype=float)
    return pd.DataFrame(
        {"Open": prices, "High": prices + 1, "Low": prices - 1, "Close": prices, "Volume": [1_000_000] * n},
        index=dates,
    )


def _option_chain_mock():
    calls = pd.DataFrame({
        "strike": [150.0, 155.0], "bid": [2.0, 1.5], "ask": [2.2, 1.7],
        "lastPrice": [2.1, 1.6], "impliedVolatility": [0.20, 0.22], "openInterest": [1000, 800],
    })
    puts = pd.DataFrame({
        "strike": [145.0, 140.0], "bid": [1.8, 1.2], "ask": [2.0, 1.4],
        "lastPrice": [1.9, 1.3], "impliedVolatility": [0.21, 0.23], "openInterest": [900, 700],
    })
    chain = MagicMock()
    chain.calls = calls
    chain.puts = puts
    return chain


def _mock_ticker(hist=None, info=None, options=("2030-06-20", "2030-07-18"), chain=None):
    t = MagicMock()
    t.history = MagicMock(return_value=hist if hist is not None else _hist_df())
    t.info = info if info is not None else {"longName": "Apple Inc.", "sector": "Technology", "marketCap": 3e12}
    t.options = options
    t.option_chain = MagicMock(return_value=chain or _option_chain_mock())
    return t


# ── YFinanceProvider ───────────────────────────────────────────────────────────

class TestYFinanceProviderImpl:

    @pytest.mark.asyncio
    async def test_get_quote_normal(self):
        df = _hist_df(5)
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(hist=df)):
            q = await YFinanceProvider().get_quote("AAPL")
        assert q["last_price"] == pytest.approx(104.0)
        assert q["source"] == "yfinance"
        assert q["day_change_pct"] is not None

    @pytest.mark.asyncio
    async def test_get_quote_single_row_no_prev(self):
        df = _hist_df(1)
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(hist=df)):
            q = await YFinanceProvider().get_quote("AAPL")
        assert q["last_price"] == pytest.approx(100.0)
        assert q["day_change_pct"] == pytest.approx(0.0, abs=1e-9)

    @pytest.mark.asyncio
    async def test_get_quote_empty_history_returns_empty(self):
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(hist=pd.DataFrame())):
            q = await YFinanceProvider().get_quote("AAPL")
        assert q["last_price"] is None
        assert q["source"] == "yfinance"

    @pytest.mark.asyncio
    async def test_get_quote_exception_returns_empty(self):
        t = MagicMock()
        t.history = MagicMock(side_effect=RuntimeError("network"))
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=t):
            q = await YFinanceProvider().get_quote("AAPL")
        assert q["last_price"] is None

    @pytest.mark.asyncio
    async def test_get_price_history_normal(self):
        df = _hist_df(60)
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(hist=df)):
            result = await YFinanceProvider().get_price_history("AAPL", "3mo")
        assert not result.empty
        assert "Close" in result.columns
        assert len(result) == 60

    @pytest.mark.asyncio
    async def test_get_price_history_empty_returns_empty(self):
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(hist=pd.DataFrame())):
            result = await YFinanceProvider().get_price_history("AAPL", "6mo")
        assert result.empty

    @pytest.mark.asyncio
    async def test_get_price_history_exception_returns_empty(self):
        t = MagicMock()
        t.history = MagicMock(side_effect=RuntimeError("timeout"))
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=t):
            result = await YFinanceProvider().get_price_history("AAPL", "1y")
        assert result.empty

    @pytest.mark.asyncio
    async def test_get_fundamentals_returns_fields(self):
        info = {
            "longName": "Apple Inc.", "sector": "Technology",
            "marketCap": 3_000_000_000_000, "trailingPE": 30.0,
            "forwardPE": 28.0, "revenueGrowth": 0.05, "averageVolume": 60_000_000,
        }
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(info=info)):
            f = await YFinanceProvider().get_fundamentals("AAPL")
        assert f["company_name"] == "Apple Inc."
        assert f["sector"] == "Technology"
        assert f["pe_ratio"] == pytest.approx(30.0)
        assert f["forward_pe"] == pytest.approx(28.0)
        assert f["source"] == "yfinance"

    @pytest.mark.asyncio
    async def test_get_fundamentals_empty_info_returns_nones(self):
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=_mock_ticker(info={})):
            f = await YFinanceProvider().get_fundamentals("AAPL")
        assert f["company_name"] is None
        assert f["market_cap"] is None

    @pytest.mark.asyncio
    async def test_get_fundamentals_exception_returns_empty(self):
        t = MagicMock()
        type(t).info = PropertyMock(side_effect=RuntimeError("fetch failed"))
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=t):
            f = await YFinanceProvider().get_fundamentals("AAPL")
        assert f["company_name"] is None

    @pytest.mark.asyncio
    async def test_get_option_chain_normal(self):
        ticker = _mock_ticker()
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=ticker):
            chain = await YFinanceProvider().get_option_chain("AAPL")
        assert chain["chosen_expiry"] is not None
        assert chain["calls"] is not None
        assert chain["puts"] is not None
        assert chain["source"] == "yfinance"

    @pytest.mark.asyncio
    async def test_get_option_chain_no_expiries_returns_empty(self):
        ticker = _mock_ticker(options=())
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=ticker):
            chain = await YFinanceProvider().get_option_chain("AAPL")
        assert chain["chosen_expiry"] is None

    @pytest.mark.asyncio
    async def test_get_option_chain_exception_returns_empty(self):
        t = MagicMock()
        type(t).options = PropertyMock(side_effect=RuntimeError("options unavailable"))
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=t):
            chain = await YFinanceProvider().get_option_chain("AAPL")
        assert chain["chosen_expiry"] is None

    @pytest.mark.asyncio
    async def test_get_option_chain_picks_expiry_gt_5days(self):
        # Both expiries are far future — should pick first one that is >= 5 days away
        ticker = _mock_ticker(options=("2030-06-01", "2030-07-01"))
        with patch("app.providers.yfinance_provider.yf.Ticker", return_value=ticker):
            chain = await YFinanceProvider().get_option_chain("AAPL")
        assert chain["chosen_expiry"] == "2030-06-01"


# ── PolygonProvider ────────────────────────────────────────────────────────────

class TestPolygonProviderImpl:

    @staticmethod
    def _prov() -> PolygonProvider:
        return PolygonProvider(api_key="test_key")

    # -- _get path tests -------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_403_raises(self):
        p = self._prov()
        resp = MagicMock()
        resp.status_code = 403
        p._client.get = AsyncMock(return_value=resp)
        with pytest.raises(ProviderError, match="403"):
            await p._get("/v2/test")

    @pytest.mark.asyncio
    async def test_get_429_raises(self):
        p = self._prov()
        resp = MagicMock()
        resp.status_code = 429
        p._client.get = AsyncMock(return_value=resp)
        with pytest.raises(ProviderError, match="429"):
            await p._get("/v2/test")

    @pytest.mark.asyncio
    async def test_get_network_error_raises(self):
        p = self._prov()
        p._client.get = AsyncMock(side_effect=httpx.RequestError("timeout"))
        with pytest.raises(ProviderError, match="network error"):
            await p._get("/v2/test")

    @pytest.mark.asyncio
    async def test_get_success_returns_json(self):
        p = self._prov()
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"results": []})
        p._client.get = AsyncMock(return_value=resp)
        data = await p._get("/v2/test")
        assert data == {"results": []}

    # -- get_quote -------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_quote_normal(self):
        p = self._prov()
        snap = {
            "ticker": {
                "lastTrade": {"p": 150.0},
                "day":     {"c": 150.0, "o": 148.5, "v": 50_000_000},
                "prevDay": {"c": 148.0},
                "todaysChangePerc": 1.35,
            }
        }
        p._get = AsyncMock(return_value=snap)
        q = await p.get_quote("AAPL")
        assert q["last_price"] == pytest.approx(150.0)
        assert q["previous_close"] == pytest.approx(148.0)
        assert q["open_price"] == pytest.approx(148.5)
        assert q["day_change_pct"] == pytest.approx(1.35)
        assert q["source"] == "polygon"

    @pytest.mark.asyncio
    async def test_get_quote_empty_results(self):
        p = self._prov()
        p._get = AsyncMock(return_value={"ticker": {}})
        q = await p.get_quote("AAPL")
        assert q["last_price"] is None

    @pytest.mark.asyncio
    async def test_get_quote_no_close_no_change(self):
        p = self._prov()
        # No lastTrade and no day.c → last_price is None
        snap = {"ticker": {"day": {"o": 148.0, "v": 1_000}, "prevDay": {}, "lastTrade": {}}}
        p._get = AsyncMock(return_value=snap)
        q = await p.get_quote("AAPL")
        assert q["last_price"] is None
        assert q["day_change_pct"] is None

    @pytest.mark.asyncio
    async def test_get_quote_provider_error_propagates(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ProviderError("403"))
        with pytest.raises(ProviderError):
            await p.get_quote("AAPL")

    @pytest.mark.asyncio
    async def test_get_quote_generic_exception_returns_empty(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ValueError("bad json"))
        q = await p.get_quote("AAPL")
        assert q["last_price"] is None

    # -- get_price_history -----------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_price_history_normal(self):
        p = self._prov()
        bars = [{"t": 1_700_000_000_000 + i * 86_400_000, "o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "v": 1e6}
                for i in range(10)]
        p._get = AsyncMock(return_value={"results": bars})
        df = await p.get_price_history("AAPL", "3mo")
        assert not df.empty
        assert "Close" in df.columns

    @pytest.mark.asyncio
    async def test_get_price_history_empty_results(self):
        p = self._prov()
        p._get = AsyncMock(return_value={"results": []})
        df = await p.get_price_history("AAPL", "6mo")
        assert df.empty

    @pytest.mark.asyncio
    async def test_get_price_history_unknown_period_defaults(self):
        p = self._prov()
        p._get = AsyncMock(return_value={"results": []})
        df = await p.get_price_history("AAPL", "custom_period")
        assert df.empty

    @pytest.mark.asyncio
    async def test_get_price_history_provider_error_propagates(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ProviderError("429"))
        with pytest.raises(ProviderError):
            await p.get_price_history("AAPL", "1y")

    @pytest.mark.asyncio
    async def test_get_price_history_generic_exception_returns_empty(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ValueError("bad"))
        df = await p.get_price_history("AAPL", "3mo")
        assert df.empty

    # -- get_fundamentals ------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_fundamentals_normal(self):
        p = self._prov()
        ref = {"results": {"name": "Apple Inc.", "market_cap": 3e12, "sic_description": "Computers"}}
        snap = {"ticker": {"day": {"v": 60_000_000}}}
        p._get = AsyncMock(side_effect=[ref, snap])
        p._yf_fundamentals_fallback = AsyncMock(return_value={
            "company_name": None, "sector": None, "market_cap": None,
            "pe_ratio": 28.5, "forward_pe": 26.0, "revenue_growth": 0.08,
            "avg_volume": None, "earnings_dates": None, "source": "polygon",
        })
        f = await p.get_fundamentals("AAPL")
        assert f["company_name"] == "Apple Inc."
        assert f["sector"] == "Computers"
        assert f["pe_ratio"] == pytest.approx(28.5)
        assert f["source"] == "polygon"

    @pytest.mark.asyncio
    async def test_get_fundamentals_empty_results(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=[{"results": {}}, {"ticker": {}}])
        _empty = {"company_name": None, "sector": None, "market_cap": None,
                  "pe_ratio": None, "forward_pe": None, "revenue_growth": None,
                  "avg_volume": None, "earnings_dates": None, "source": "polygon"}
        p._yf_fundamentals_fallback = AsyncMock(return_value=_empty)
        f = await p.get_fundamentals("AAPL")
        assert f["company_name"] is None
        assert f["market_cap"] is None

    @pytest.mark.asyncio
    async def test_get_fundamentals_provider_error_propagates(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ProviderError("403"))
        with pytest.raises(ProviderError):
            await p.get_fundamentals("AAPL")

    @pytest.mark.asyncio
    async def test_get_fundamentals_generic_exception_returns_empty(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ValueError("bad"))
        _empty = {"company_name": None, "sector": None, "market_cap": None,
                  "pe_ratio": None, "forward_pe": None, "revenue_growth": None,
                  "avg_volume": None, "earnings_dates": None, "source": "polygon"}
        p._yf_fundamentals_fallback = AsyncMock(return_value=_empty)
        f = await p.get_fundamentals("AAPL")
        assert f["company_name"] is None

    # -- get_option_chain ------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_option_chain_with_iv(self):
        p = self._prov()
        contracts = [
            {"details": {"expiration_date": "2030-06-20", "contract_type": "call", "strike_price": 150.0},
             "day": {"close": 2.0, "last_quote": {"ask": 2.1}},
             "greeks": {"implied_volatility": 0.20}, "open_interest": 1000},
            {"details": {"expiration_date": "2030-06-20", "contract_type": "put", "strike_price": 145.0},
             "day": {"close": 1.8, "last_quote": {}},
             "greeks": {"implied_volatility": 0.21}, "open_interest": 800},
        ]
        p._get = AsyncMock(return_value={"results": contracts})
        chain = await p.get_option_chain("AAPL")
        assert chain["chosen_expiry"] == "2030-06-20"
        assert chain["calls"] is not None
        assert chain["source"] == "polygon"

    @pytest.mark.asyncio
    async def test_get_option_chain_no_iv_falls_back_to_yfinance(self):
        p = self._prov()
        contracts = [
            {"details": {"expiration_date": "2030-06-20", "contract_type": "call", "strike_price": 150.0},
             "day": {"close": 2.0, "last_quote": {}},
             "greeks": {}, "open_interest": 1000},
        ]
        p._get = AsyncMock(return_value={"results": contracts})
        yf_chain = {
            "expiries": ["2030-06-20"], "chosen_expiry": "2030-06-20", "spot": 148.0,
            "calls": pd.DataFrame({"strike": [150.0], "impliedVolatility": [0.20]}),
            "puts": None, "atm_iv": None, "chain_liquidity_hint": "unknown",
            "implied_move_1d_pct": None, "source": "yfinance",
        }
        with patch("app.providers.yfinance_provider.YFinanceProvider.get_option_chain",
                   AsyncMock(return_value=yf_chain)):
            chain = await p.get_option_chain("AAPL")
        assert "yfinance" in chain["source"]

    @pytest.mark.asyncio
    async def test_get_option_chain_empty_falls_back(self):
        p = self._prov()
        p._get = AsyncMock(return_value={"results": []})
        yf_chain = {
            "expiries": [], "chosen_expiry": None, "spot": None,
            "calls": None, "puts": None, "atm_iv": None,
            "chain_liquidity_hint": "unknown", "implied_move_1d_pct": None, "source": "yfinance",
        }
        with patch("app.providers.yfinance_provider.YFinanceProvider.get_option_chain",
                   AsyncMock(return_value=yf_chain)):
            chain = await p.get_option_chain("AAPL")
        assert chain["chosen_expiry"] is None

    @pytest.mark.asyncio
    async def test_get_option_chain_provider_error_propagates(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ProviderError("403"))
        with pytest.raises(ProviderError):
            await p.get_option_chain("AAPL")

    @pytest.mark.asyncio
    async def test_get_option_chain_generic_exception_falls_back(self):
        p = self._prov()
        p._get = AsyncMock(side_effect=ValueError("parse error"))
        yf_chain = {
            "expiries": [], "chosen_expiry": None, "spot": None,
            "calls": None, "puts": None, "atm_iv": None,
            "chain_liquidity_hint": "unknown", "implied_move_1d_pct": None, "source": "yfinance",
        }
        with patch("app.providers.yfinance_provider.YFinanceProvider.get_option_chain",
                   AsyncMock(return_value=yf_chain)):
            chain = await p.get_option_chain("AAPL")
        assert chain["chosen_expiry"] is None

    @pytest.mark.asyncio
    async def test_aclose(self):
        p = self._prov()
        p._client.aclose = AsyncMock()
        await p.aclose()
        p._client.aclose.assert_awaited_once()


# ── RedisCache — extended paths ───────────────────────────────────────────────

class TestRedisCacheExtended:

    @staticmethod
    def _cache(inner=None):
        from app.providers.redis_cache import RedisCache
        return RedisCache(inner=inner or AsyncMock(), redis_url="redis://localhost:6380/0")

    @pytest.mark.asyncio
    async def test_get_swallows_redis_error(self):
        cache = self._cache()
        cache._redis.get = AsyncMock(side_effect=Exception("connection refused"))
        result = await cache._get("some:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_swallows_redis_error(self):
        cache = self._cache()
        cache._redis.setex = AsyncMock(side_effect=Exception("connection refused"))
        await cache._set("some:key", {"a": 1}, 60)  # must not raise

    @pytest.mark.asyncio
    async def test_get_price_history_cache_hit(self):
        df = _hist_df(10)
        cached = json.loads(df.to_json(orient="split"))
        cache = self._cache()
        cache._get = AsyncMock(return_value=cached)
        cache._set = AsyncMock()
        result = await cache.get_price_history("AAPL", "3mo")
        assert not result.empty
        cache._inner.get_price_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_price_history_cache_miss(self):
        df = _hist_df(10)
        inner = AsyncMock()
        inner.get_price_history = AsyncMock(return_value=df)
        cache = self._cache(inner)
        cache._get = AsyncMock(return_value=None)
        cache._set = AsyncMock()
        result = await cache.get_price_history("AAPL", "3mo")
        assert not result.empty
        inner.get_price_history.assert_awaited_once()
        cache._set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_price_history_corrupted_cache_falls_through(self):
        df = _hist_df(5)
        inner = AsyncMock()
        inner.get_price_history = AsyncMock(return_value=df)
        cache = self._cache(inner)
        cache._get = AsyncMock(return_value="not_a_valid_dict")
        cache._set = AsyncMock()
        result = await cache.get_price_history("AAPL", "3mo")
        inner.get_price_history.assert_awaited_once()
        assert not result.empty

    @pytest.mark.asyncio
    async def test_get_price_history_empty_df_not_cached(self):
        inner = AsyncMock()
        inner.get_price_history = AsyncMock(return_value=pd.DataFrame())
        cache = self._cache(inner)
        cache._get = AsyncMock(return_value=None)
        cache._set = AsyncMock()
        result = await cache.get_price_history("AAPL", "3mo")
        assert result.empty
        cache._set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_fundamentals_cache_hit(self):
        cached = {"company_name": "Apple Inc.", "source": "yfinance"}
        cache = self._cache()
        cache._get = AsyncMock(return_value=cached)
        result = await cache.get_fundamentals("AAPL")
        assert result == cached
        cache._inner.get_fundamentals.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_fundamentals_cache_miss(self):
        fetched = {"company_name": "Apple Inc.", "source": "yfinance"}
        inner = AsyncMock()
        inner.get_fundamentals = AsyncMock(return_value=fetched)
        cache = self._cache(inner)
        cache._get = AsyncMock(return_value=None)
        cache._set = AsyncMock()
        result = await cache.get_fundamentals("AAPL")
        assert result == fetched
        cache._set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_option_chain_cache_hit_with_dataframe(self):
        calls_df = pd.DataFrame({"strike": [150.0], "impliedVolatility": [0.20]})
        cached = {
            "expiries": ["2030-06-20"], "chosen_expiry": "2030-06-20", "spot": 148.0,
            "calls": json.loads(calls_df.to_json(orient="split")),
            "puts": None, "atm_iv": None, "chain_liquidity_hint": "unknown",
            "implied_move_1d_pct": None, "source": "yfinance",
        }
        cache = self._cache()
        cache._get = AsyncMock(return_value=cached)
        result = await cache.get_option_chain("AAPL")
        assert result["chosen_expiry"] == "2030-06-20"
        assert isinstance(result["calls"], pd.DataFrame)
        cache._inner.get_option_chain.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_option_chain_cache_hit_corrupt_df_set_to_none(self):
        cached = {
            "expiries": ["2030-06-20"], "chosen_expiry": "2030-06-20", "spot": 148.0,
            "calls": "not_a_valid_df", "puts": None, "atm_iv": None,
            "chain_liquidity_hint": "unknown", "implied_move_1d_pct": None, "source": "yfinance",
        }
        cache = self._cache()
        cache._get = AsyncMock(return_value=cached)
        result = await cache.get_option_chain("AAPL")
        assert result["calls"] is None  # corrupt data handled

    @pytest.mark.asyncio
    async def test_get_option_chain_cache_miss(self):
        calls_df = pd.DataFrame({"strike": [150.0], "impliedVolatility": [0.20]})
        fetched = {
            "expiries": ["2030-06-20"], "chosen_expiry": "2030-06-20", "spot": 148.0,
            "calls": calls_df, "puts": None, "atm_iv": None,
            "chain_liquidity_hint": "unknown", "implied_move_1d_pct": None, "source": "yfinance",
        }
        inner = AsyncMock()
        inner.get_option_chain = AsyncMock(return_value=fetched)
        cache = self._cache(inner)
        cache._get = AsyncMock(return_value=None)
        cache._set = AsyncMock()
        result = await cache.get_option_chain("AAPL")
        assert result["chosen_expiry"] == "2030-06-20"
        inner.get_option_chain.assert_awaited_once()
        cache._set.assert_awaited_once()
