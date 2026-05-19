"""Tests for new main.py endpoints: history and ingest warm — no DB, no network."""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient

from app.main import _batch_row_to_response, _resolve_universe, app
from app.schemas.batch import BatchJobRequest, BatchJobStatus


def _fake_run(
    symbol: str = "AAPL",
    instrument_recommendation: str = "stock",
    last_price: float = 150.0,
    score: float = 0.4,
) -> MagicMock:
    row = MagicMock()
    row.id = uuid.uuid4()
    row.symbol = symbol
    row.started_at = datetime(2025, 5, 1, tzinfo=UTC)
    row.finished_at = datetime(2025, 5, 1, 0, 1, tzinfo=UTC)
    row.instrument_recommendation = instrument_recommendation
    row.confidence_note = "test note"
    row.last_price = last_price
    row.status = "complete"
    row.verdict_json = {"decision_aids": {"stock_vs_options_score": score}}
    return row


async def _session_with_runs(runs: list):
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = runs
    session.execute = AsyncMock(return_value=result)
    yield session


def _mk_session(runs: list):
    def _factory():
        return _session_with_runs(runs)
    return _factory


@pytest.fixture(autouse=True)
def _patch_lifespan_deps(monkeypatch):
    monkeypatch.setattr("app.db.session.init_engine", lambda: None)
    monkeypatch.setattr("app.observability.configure_otel", lambda: None)
    monkeypatch.setattr("app.main.configure_otel", lambda: None)


# ---------------------------------------------------------------------------
# GET /v1/analysis/history/{symbol}
# ---------------------------------------------------------------------------


def test_history_returns_items(monkeypatch):
    run = _fake_run("AAPL", "stock", 150.0, 0.4)
    monkeypatch.setattr("app.main.get_session", _mk_session([run]))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/history/AAPL")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["instrument_recommendation"] == "stock"
    assert data[0]["stock_vs_options_score"] == pytest.approx(0.4)


def test_history_empty_when_no_runs(monkeypatch):
    monkeypatch.setattr("app.main.get_session", _mk_session([]))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/history/MSFT")

    assert resp.status_code == 200
    assert resp.json() == []


def test_history_handles_missing_score(monkeypatch):
    run = _fake_run()
    run.verdict_json = None  # old run without verdict_json
    monkeypatch.setattr("app.main.get_session", _mk_session([run]))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/history/AAPL")

    assert resp.status_code == 200
    assert resp.json()[0]["stock_vs_options_score"] is None


def test_history_handles_malformed_verdict_json(monkeypatch):
    run = _fake_run()
    run.verdict_json = {"no_decision_aids": True}
    monkeypatch.setattr("app.main.get_session", _mk_session([run]))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/history/AAPL")

    assert resp.status_code == 200
    assert resp.json()[0]["stock_vs_options_score"] is None


def test_history_symbol_uppercased(monkeypatch):
    run = _fake_run("AAPL")
    monkeypatch.setattr("app.main.get_session", _mk_session([run]))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/history/aapl")

    assert resp.status_code == 200


def test_history_limit_param(monkeypatch):
    runs = [_fake_run() for _ in range(5)]
    monkeypatch.setattr("app.main.get_session", _mk_session(runs))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/history/AAPL?limit=5")

    assert resp.status_code == 200
    assert len(resp.json()) == 5


# ---------------------------------------------------------------------------
# POST /v1/ingest/warm
# ---------------------------------------------------------------------------


def test_ingest_warm_no_redis(monkeypatch):
    monkeypatch.setattr("app.main.settings.use_redis", False)

    with TestClient(app) as client:
        resp = client.post("/v1/ingest/warm", json=["AAPL", "MSFT"])

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "queued"
    assert data["count"] == "2"


def test_ingest_warm_with_redis(monkeypatch):
    monkeypatch.setattr("app.main.settings.use_redis", True)
    monkeypatch.setattr("app.main.build_provider", MagicMock(return_value=MagicMock()))
    monkeypatch.setattr("app.main.warm_cache", AsyncMock())

    with TestClient(app) as client:
        resp = client.post("/v1/ingest/warm", json=["AAPL"])

    assert resp.status_code == 202
    assert resp.json()["count"] == "1"


def test_ingest_warm_empty_list(monkeypatch):
    monkeypatch.setattr("app.main.settings.use_redis", False)

    with TestClient(app) as client:
        resp = client.post("/v1/ingest/warm", json=[])

    assert resp.status_code == 202
    assert resp.json()["count"] == "0"


# ---------------------------------------------------------------------------
# GET /healthz
# ---------------------------------------------------------------------------


def test_healthz():
    with TestClient(app) as client:
        resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# _resolve_universe helper
# ---------------------------------------------------------------------------


def test_resolve_universe_top10():
    from app.universe import TOP_10
    req = BatchJobRequest(universe="top10")
    symbols = _resolve_universe(req)
    assert len(symbols) == 10
    assert symbols == list(TOP_10)


def test_resolve_universe_top100():
    req = BatchJobRequest(universe="top100")
    symbols = _resolve_universe(req)
    assert len(symbols) == 100


def test_resolve_universe_full():
    req = BatchJobRequest(universe="full")
    symbols = _resolve_universe(req)
    assert len(symbols) >= 500


def test_resolve_universe_custom():
    req = BatchJobRequest(universe="custom", symbols=["AAPL", "TSLA"])
    symbols = _resolve_universe(req)
    assert "AAPL" in symbols
    assert "TSLA" in symbols


def test_resolve_universe_custom_no_symbols():
    req = BatchJobRequest(universe="custom")
    with pytest.raises(HTTPException) as exc_info:
        _resolve_universe(req)
    assert exc_info.value.status_code == 422


def test_resolve_universe_unknown():
    req = BatchJobRequest(universe="unknown_universe")
    with pytest.raises(HTTPException) as exc_info:
        _resolve_universe(req)
    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# _batch_row_to_response helper
# ---------------------------------------------------------------------------


def test_batch_row_to_response_with_composition_as_of():
    row = MagicMock()
    row.id = uuid.uuid4()
    row.status = "complete"
    row.universe = "top10"
    row.total_symbols = 10
    row.completed_symbols = 10
    row.failed_symbols = 0
    row.composition_as_of = date(2025, 1, 15)
    row.requested_at = datetime(2025, 1, 15, tzinfo=UTC)
    row.finished_at = datetime(2025, 1, 15, 0, 5, tzinfo=UTC)
    resp = _batch_row_to_response(row)
    assert resp.status == BatchJobStatus.complete
    assert resp.composition_as_of == "2025-01-15"


def test_batch_row_to_response_without_composition_as_of():
    row = MagicMock()
    row.id = uuid.uuid4()
    row.status = "pending"
    row.universe = "top100"
    row.total_symbols = 100
    row.completed_symbols = 0
    row.failed_symbols = 0
    row.composition_as_of = None
    row.requested_at = datetime(2025, 1, 15, tzinfo=UTC)
    row.finished_at = None
    resp = _batch_row_to_response(row)
    assert resp.composition_as_of is None


# ---------------------------------------------------------------------------
# Alert router endpoints (via TestClient + dependency override)
# ---------------------------------------------------------------------------


def _mock_api_key():
    key = MagicMock()
    key.id = uuid.uuid4()
    return key


# ---------------------------------------------------------------------------
# POST /v1/analysis/run and GET /v1/analysis/run/{symbol}
# ---------------------------------------------------------------------------


def _mock_verdict():
    from app.schemas.agents import (
        AgentContribution,
        AgentStatus,
        DataFreshness,
        DecisionAids,
        InstrumentRecommendation,
        SupervisorVerdict,
        VolatilityContext,
    )

    return SupervisorVerdict(
        instrument_recommendation=InstrumentRecommendation.stock,
        confidence_note="test",
        agent_contributions=[
            AgentContribution(agent_name="MarketDataAgent", status=AgentStatus.complete, headline="ok")
        ],
        data_freshness=DataFreshness(),
        decision_aids=DecisionAids(
            summary_headline="test",
            stock_vs_options_score=0.3,
            volatility=VolatilityContext(regime="normal"),
        ),
    )


def test_run_analysis_post(monkeypatch):
    monkeypatch.setattr("app.main._supervisor.run_analysis", AsyncMock(return_value=_mock_verdict()))

    with TestClient(app) as client:
        resp = client.post("/v1/analysis/run", json={"symbol": "AAPL"})

    assert resp.status_code == 200
    assert resp.json()["instrument_recommendation"] == "stock"


def test_run_analysis_get(monkeypatch):
    monkeypatch.setattr("app.main._supervisor.run_analysis", AsyncMock(return_value=_mock_verdict()))

    with TestClient(app) as client:
        resp = client.get("/v1/analysis/run/AAPL")

    assert resp.status_code == 200
    assert resp.json()["instrument_recommendation"] == "stock"


# ---------------------------------------------------------------------------
# GET /v1/analysis/batch/{job_id}
# ---------------------------------------------------------------------------


def _mk_batch_session(row):
    async def _gen():
        session = AsyncMock()
        session.get = AsyncMock(return_value=row)
        yield session
    return _gen


def test_get_batch_status_found(monkeypatch):
    row = MagicMock()
    row.id = uuid.uuid4()
    row.status = "running"
    row.universe = "top10"
    row.total_symbols = 10
    row.completed_symbols = 3
    row.failed_symbols = 0
    row.composition_as_of = None
    row.requested_at = datetime(2025, 1, 1, tzinfo=UTC)
    row.finished_at = None

    monkeypatch.setattr("app.main.get_session", _mk_batch_session(row))

    with TestClient(app) as client:
        resp = client.get(f"/v1/analysis/batch/{row.id}")

    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_get_batch_status_not_found(monkeypatch):
    monkeypatch.setattr("app.main.get_session", _mk_batch_session(None))

    with TestClient(app) as client:
        resp = client.get(f"/v1/analysis/batch/{uuid.uuid4()}")

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auth router functions (direct call)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_key_direct():
    from app.routers.auth import create_key
    from app.schemas.user import ApiKeyCreate

    req = ApiKeyCreate(name="my-key")

    async def _refresh(row):
        row.id = uuid.uuid4()
        row.is_active = True
        row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        row.key_prefix = row.key_prefix or "sk-12345"

    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=_refresh)

    from app.schemas.user import ApiKeyResponse
    result = await create_key(req=req, session=session)
    assert isinstance(result, ApiKeyResponse)
    assert result.name == "my-key"
    assert result.key.startswith("sk-")


@pytest.mark.asyncio
async def test_list_keys_direct():
    from app.routers.auth import list_keys

    key = MagicMock()
    key.key_prefix = "sk-123456"

    key_row = MagicMock()
    key_row.id = uuid.uuid4()
    key_row.name = "test-key"
    key_row.key_prefix = "sk-123456"
    key_row.is_active = True
    key_row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    key_row.last_used_at = None

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [key_row]
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result_mock)

    results = await list_keys(current_key=key, session=session)
    assert len(results) == 1
    assert results[0].name == "test-key"


@pytest.mark.asyncio
async def test_revoke_key_direct():
    from app.routers.auth import revoke_key

    key = MagicMock()
    key.key_prefix = "sk-123456"

    row = MagicMock()
    row.id = uuid.uuid4()
    row.key_prefix = "sk-123456"
    row.is_active = True

    session = AsyncMock()
    session.get = AsyncMock(return_value=row)
    session.commit = AsyncMock()

    await revoke_key(key_id=row.id, current_key=key, session=session)
    assert row.is_active is False
