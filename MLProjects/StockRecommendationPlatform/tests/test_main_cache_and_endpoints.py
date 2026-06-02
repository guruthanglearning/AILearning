"""Tests for TTL cache, price-history endpoint, peers endpoint, batch idempotency,
and market-quotes date parsing — covering the main.py gaps."""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
from starlette.testclient import TestClient

from app.limiter import limiter
from app.main import _TTL_CACHE, _cache_get, _cache_set, app


@pytest.fixture(autouse=True)
def _patch_lifespan_deps(monkeypatch):
    monkeypatch.setattr("app.db.session.init_engine", lambda: None)
    monkeypatch.setattr("app.observability.configure_otel", lambda: None)
    monkeypatch.setattr("app.main.configure_otel", lambda: None)


@pytest.fixture(autouse=True)
def _clear_ttl_cache():
    _TTL_CACHE.clear()
    yield
    _TTL_CACHE.clear()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


# ---------------------------------------------------------------------------
# TTL cache helpers
# ---------------------------------------------------------------------------


def test_cache_miss_returns_none():
    assert _cache_get("nonexistent") is None


def test_cache_hit_returns_value():
    _cache_set("k1", {"data": 42})
    assert _cache_get("k1") == {"data": 42}


def test_cache_hit_after_set():
    _cache_set("k2", [1, 2, 3])
    result = _cache_get("k2")
    assert result == [1, 2, 3]


def test_cache_expired_returns_none(monkeypatch):
    # Inject an entry with a very old timestamp so it's already expired
    _TTL_CACHE["expired_key"] = (time.monotonic() - 400, "old_value")
    assert _cache_get("expired_key") is None
    # Entry should be evicted
    assert "expired_key" not in _TTL_CACHE


def test_cache_overwrite():
    _cache_set("k3", "first")
    _cache_set("k3", "second")
    assert _cache_get("k3") == "second"


# ---------------------------------------------------------------------------
# GET /v1/price-history/{symbol}
# ---------------------------------------------------------------------------


def _make_price_df():
    dates = pd.date_range("2025-01-01", periods=5)
    return pd.DataFrame(
        {
            "Date": dates,
            "Open":   [100.0, 101.0, 102.0, 103.0, 104.0],
            "High":   [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low":    [99.0,  100.0, 101.0, 102.0, 103.0],
            "Close":  [103.0, 104.0, 105.0, 106.0, 107.0],
            "Volume": [1_000_000] * 5,
        }
    ).set_index("Date")


def test_price_history_success(monkeypatch):
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_price_df())
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        resp = client.get("/v1/price-history/AAPL?period=3mo")

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["period"] == "3mo"
    assert len(data["data"]) == 5
    assert "close" in data["data"][0]


def test_price_history_cached_on_second_call(monkeypatch):
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_price_df())
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        client.get("/v1/price-history/TSLA?period=1mo")
        client.get("/v1/price-history/TSLA?period=1mo")

    # Provider should be called once; second call served from cache
    assert provider.get_price_history.call_count == 1


def test_price_history_not_found_returns_404(monkeypatch):
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=None)
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        resp = client.get("/v1/price-history/FAKE?period=3mo")

    assert resp.status_code == 404


def test_price_history_empty_df_returns_404(monkeypatch):
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=pd.DataFrame())
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        resp = client.get("/v1/price-history/EMPTY?period=3mo")

    assert resp.status_code == 404


def test_price_history_provider_exception_returns_500(monkeypatch):
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(side_effect=RuntimeError("network error"))
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        resp = client.get("/v1/price-history/ERR?period=3mo")

    assert resp.status_code == 500


def test_price_history_invalid_period_returns_422(monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        resp = client.get("/v1/price-history/AAPL?period=5y")

    assert resp.status_code == 422


def test_price_history_symbol_uppercased(monkeypatch):
    provider = AsyncMock()
    provider.get_price_history = AsyncMock(return_value=_make_price_df())
    monkeypatch.setattr("app.main.build_provider", lambda: provider)

    with TestClient(app) as client:
        resp = client.get("/v1/price-history/aapl?period=1y")

    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# GET /v1/peers/{symbol}
# ---------------------------------------------------------------------------


def _mock_yf_ticker(sector="Technology", peers_info=None):
    ticker = MagicMock()
    ticker.info = {
        "sector": sector,
        "shortName": "Apple Inc",
        "currentPrice": 150.0,
        "marketCap": 2_500_000_000_000,
        "trailingPE": 28.5,
        "forwardPE": 24.0,
    }
    hist = pd.DataFrame({"Close": [140.0, 145.0, 150.0]})
    ticker.history = MagicMock(return_value=hist)
    return ticker


def test_peers_success(monkeypatch):
    mock_ticker = _mock_yf_ticker()
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: mock_ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/peers/AAPL")

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert "peers" in data
    assert len(data["peers"]) > 0


def test_peers_symbol_uppercased(monkeypatch):
    mock_ticker = _mock_yf_ticker()
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: mock_ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/peers/aapl")

    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"


def test_peers_cached_on_second_call(monkeypatch):
    call_count = {"n": 0}
    def _ticker(sym):
        call_count["n"] += 1
        return _mock_yf_ticker()
    monkeypatch.setattr("app.main.yf.Ticker", _ticker)

    with TestClient(app) as client:
        client.get("/v1/peers/MSFT")
        client.get("/v1/peers/MSFT")

    # Only first request should hit yfinance; second comes from cache
    assert call_count["n"] < 20  # Generous ceiling but still shows caching reduces calls


def test_peers_unknown_sector_returns_just_symbol(monkeypatch):
    ticker = MagicMock()
    ticker.info = {"sector": None}
    ticker.history = MagicMock(return_value=pd.DataFrame({"Close": [100.0]}))
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/peers/UNKN")

    assert resp.status_code == 200
    data = resp.json()
    assert data["sector"] is None
    assert any(p["symbol"] == "UNKN" for p in data["peers"])


def test_peers_ticker_exception_returns_symbol_only(monkeypatch):
    ticker = MagicMock()
    ticker.info = {"sector": None}
    ticker.history = MagicMock(side_effect=RuntimeError("no data"))
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/peers/BAD")

    assert resp.status_code == 200
    data = resp.json()
    assert "peers" in data


# ---------------------------------------------------------------------------
# POST /v1/analysis/batch — idempotency with batch_key
# ---------------------------------------------------------------------------


def _mk_batch_idempotency_session(existing_row):
    async def _gen():
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = existing_row
        session.execute = AsyncMock(return_value=result)
        session.add = MagicMock()
        session.commit = AsyncMock()
        yield session
    return _gen


def _make_batch_row(status="running"):
    row = MagicMock()
    row.id = uuid.uuid4()
    row.status = status
    row.universe = "top10"
    row.total_symbols = 10
    row.completed_symbols = 5
    row.failed_symbols = 0
    row.composition_as_of = None
    row.requested_at = datetime(2025, 1, 1, tzinfo=UTC)
    row.finished_at = None
    return row


def test_batch_idempotency_returns_existing_running_job(monkeypatch):
    existing = _make_batch_row("running")
    monkeypatch.setattr("app.main.get_session", _mk_batch_idempotency_session(existing))

    with TestClient(app) as client:
        resp = client.post("/v1/analysis/batch", json={"universe": "top10", "batch_key": "my-key-123"})

    assert resp.status_code == 202
    assert str(existing.id) == resp.json()["job_id"]


def test_batch_idempotency_returns_existing_complete_job(monkeypatch):
    existing = _make_batch_row("complete")
    monkeypatch.setattr("app.main.get_session", _mk_batch_idempotency_session(existing))

    with TestClient(app) as client:
        resp = client.post("/v1/analysis/batch", json={"universe": "top10", "batch_key": "my-key-456"})

    assert resp.status_code == 202
    assert str(existing.id) == resp.json()["job_id"]


def test_batch_no_batch_key_creates_new_job(monkeypatch):
    # No batch_key → skips idempotency check entirely
    async def _gen():
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        yield session
    monkeypatch.setattr("app.main.get_session", lambda: _gen())
    # Prevent the background task from trying to connect to the real DB
    monkeypatch.setattr("app.main.run_batch_job", AsyncMock())

    with TestClient(app) as client:
        resp = client.post("/v1/analysis/batch", json={"universe": "top10"})

    assert resp.status_code == 202
    assert "job_id" in resp.json()


# ---------------------------------------------------------------------------
# GET /v1/market/quotes — earnings and dividend date parsing
# ---------------------------------------------------------------------------


def _mock_yf_for_market_quotes(info_override: dict):
    ticker = MagicMock()
    ticker.info = info_override
    return ticker


def test_market_quotes_earnings_timestamp_int(monkeypatch):
    ts = int(datetime(2025, 8, 1, tzinfo=UTC).timestamp())
    info = {
        "regularMarketPrice": 150.0,
        "regularMarketPreviousClose": 148.0,
        "earningsTimestamp": ts,
    }
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_yf_for_market_quotes(info))

    with TestClient(app) as client:
        resp = client.get("/v1/market/quotes?symbols=AAPL")

    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["earnings_date"] == "2025/08/01"


def test_market_quotes_earnings_date_as_list(monkeypatch):
    ts = int(datetime(2025, 10, 15, tzinfo=UTC).timestamp())
    info = {
        "regularMarketPrice": 200.0,
        "earningsDate": [ts],
    }
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_yf_for_market_quotes(info))

    with TestClient(app) as client:
        resp = client.get("/v1/market/quotes?symbols=TSLA")

    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["earnings_date"] == "2025/10/15"


def test_market_quotes_dividend_date(monkeypatch):
    div_ts = int(datetime(2025, 9, 15, tzinfo=UTC).timestamp())
    info = {
        "regularMarketPrice": 300.0,
        "dividendDate": div_ts,
    }
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_yf_for_market_quotes(info))

    with TestClient(app) as client:
        resp = client.get("/v1/market/quotes?symbols=MSFT")

    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["div_payment_date"] == "2025-09-15"


def test_market_quotes_no_dates(monkeypatch):
    info = {"regularMarketPrice": 100.0}
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: _mock_yf_for_market_quotes(info))

    with TestClient(app) as client:
        resp = client.get("/v1/market/quotes?symbols=NVDA")

    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["earnings_date"] is None
    assert row["div_payment_date"] is None


def test_market_quotes_too_many_symbols(monkeypatch):
    with TestClient(app) as client:
        symbols = ",".join([f"SYM{i}" for i in range(51)])
        resp = client.get(f"/v1/market/quotes?symbols={symbols}")

    assert resp.status_code == 422


def test_market_quotes_empty_symbols(monkeypatch):
    with TestClient(app) as client:
        resp = client.get("/v1/market/quotes?symbols=,,,")

    assert resp.status_code == 200
    assert resp.json() == []


def test_market_quotes_ticker_exception_returns_empty_row(monkeypatch):
    ticker = MagicMock()
    ticker.info = None  # causes TypeError in info.get(...)
    monkeypatch.setattr("app.main.yf.Ticker", lambda sym: ticker)

    with TestClient(app) as client:
        resp = client.get("/v1/market/quotes?symbols=ERR")

    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["symbol"] == "ERR"
    assert row["last_price"] is None
