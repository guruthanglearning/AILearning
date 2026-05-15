"""Batch-job offline tests — no DB, no network."""
from __future__ import annotations

import uuid

import pytest

from app.schemas.batch import BatchJobRequest, BatchJobStatus
from app.universe import TOP_10, TOP_100, get_sp500, get_top_n


# ---------------------------------------------------------------------------
# Universe resolution
# ---------------------------------------------------------------------------


def test_resolve_universe_top10():
    assert len(TOP_10) == 10
    assert TOP_10[0] == "AAPL"


def test_resolve_universe_top100():
    assert len(TOP_100) == 100
    assert "AAPL" in TOP_100


def test_resolve_universe_full():
    symbols = get_sp500()
    assert len(symbols) >= 500
    # no duplicates
    assert len(symbols) == len(set(symbols))


def test_resolve_universe_custom_via_request():
    req = BatchJobRequest(universe="custom", symbols=["AAPL", "TSLA"])
    assert req.symbols == ["AAPL", "TSLA"]
    assert req.universe == "custom"


def test_get_top_n():
    n5 = get_top_n(5)
    assert len(n5) == 5
    assert n5 == TOP_10[:5]


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def test_batch_job_request_idempotency_key():
    key = "daily-run-2025-01-15"
    req = BatchJobRequest(universe="top10", batch_key=key)
    assert req.batch_key == key
    assert req.universe == "top10"
    assert req.symbols is None


def test_batch_job_request_defaults():
    req = BatchJobRequest()
    assert req.universe == "top10"
    assert req.batch_key is None
    assert req.portfolio_value_usd is None


def test_batch_job_status_enum_values():
    assert BatchJobStatus.pending == "pending"
    assert BatchJobStatus.running == "running"
    assert BatchJobStatus.complete == "complete"
    assert BatchJobStatus.partial == "partial"
    assert BatchJobStatus.failed == "failed"
