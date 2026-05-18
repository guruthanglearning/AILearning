"""Phase 5 observability offline tests — no DB, no Redis, no OTel collector."""
from __future__ import annotations

import json
import uuid

# ---------------------------------------------------------------------------
# Correlation ID helpers
# ---------------------------------------------------------------------------

def test_is_valid_uuid_helper():
    from app.middleware import _is_valid_uuid
    assert _is_valid_uuid(str(uuid.uuid4())) is True
    assert _is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True
    assert _is_valid_uuid("not-a-uuid") is False
    assert _is_valid_uuid("") is False
    assert _is_valid_uuid(None) is False


def test_middleware_injects_correlation_id_header():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from app.middleware import CorrelationIdMiddleware, _is_valid_uuid

    async def homepage(request: Request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(CorrelationIdMiddleware)

    with TestClient(app) as client:
        resp = client.get("/")

    assert resp.status_code == 200
    assert "X-Correlation-ID" in resp.headers
    assert _is_valid_uuid(resp.headers["X-Correlation-ID"])


def test_middleware_echoes_valid_incoming_header():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from app.middleware import CorrelationIdMiddleware

    async def homepage(request: Request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(CorrelationIdMiddleware)

    known = "550e8400-e29b-41d4-a716-446655440000"
    with TestClient(app) as client:
        resp = client.get("/", headers={"X-Correlation-ID": known})

    assert resp.headers["X-Correlation-ID"] == known


def test_middleware_rejects_invalid_header():
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from app.middleware import CorrelationIdMiddleware, _is_valid_uuid

    async def homepage(request: Request):
        return JSONResponse({"ok": True})

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(CorrelationIdMiddleware)

    with TestClient(app) as client:
        resp = client.get("/", headers={"X-Correlation-ID": "garbage-not-a-uuid"})

    cid = resp.headers["X-Correlation-ID"]
    assert cid != "garbage-not-a-uuid"
    assert _is_valid_uuid(cid)


# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

def test_structlog_emits_json_with_correlation_id(capfd, monkeypatch):
    import structlog.contextvars

    import app.observability as obs_mod

    # Reset the idempotency flag so configure_logging() re-wires handlers
    monkeypatch.setattr(obs_mod, "_logging_configured", False)
    obs_mod.configure_logging()

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id="test-cid-abc")

    import structlog as sl
    logger = sl.get_logger("test_logger")
    logger.info("hello_world", extra_field="value")

    captured = capfd.readouterr()
    lines = [ln for ln in captured.out.strip().splitlines() if ln.strip()]
    assert lines, "No log output captured on stdout"
    parsed = json.loads(lines[-1])
    assert parsed.get("correlation_id") == "test-cid-abc"
    assert parsed.get("event") == "hello_world"
    assert "timestamp" in parsed

    structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

def test_agent_latency_histogram_labels():
    from app.observability import agent_latency_histogram
    from app.schemas.agents import AgentStatus

    agent_latency_histogram.labels(
        agent_name="MarketDataAgent",
        status=AgentStatus.complete.value,
    ).observe(0.123)
    agent_latency_histogram.labels(
        agent_name="TechnicalsAgent",
        status=AgentStatus.failed.value,
    ).observe(45.1)

    assert set(agent_latency_histogram._labelnames) == {"agent_name", "status"}


def test_batch_symbols_counter_labels():
    from app.observability import batch_symbols_counter

    batch_symbols_counter.labels(outcome="completed").inc()
    batch_symbols_counter.labels(outcome="failed").inc()

    assert set(batch_symbols_counter._labelnames) == {"outcome"}


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

def test_observability_config_defaults(monkeypatch):
    for var in ("LOG_LEVEL", "OTEL_ENABLED", "OTEL_ENDPOINT", "METRICS_ENABLED"):
        monkeypatch.delenv(var, raising=False)

    from app.config import Settings
    s = Settings()
    assert s.log_level == "INFO"
    assert s.otel_enabled is False
    assert s.otel_endpoint == ""
    assert s.metrics_enabled is True
