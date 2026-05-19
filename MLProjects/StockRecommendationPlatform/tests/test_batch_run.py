"""Tests for run_batch_job and _run_single_symbol — mocked DB and supervisor."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.batch import _increment_counter, _run_single_symbol, run_batch_job
from app.schemas.agents import (
    AgentContribution,
    AgentStatus,
    DataFreshness,
    DecisionAids,
    InstrumentRecommendation,
    SupervisorVerdict,
    VolatilityContext,
)


def _mock_verdict() -> SupervisorVerdict:
    return SupervisorVerdict(
        instrument_recommendation=InstrumentRecommendation.stock,
        confidence_note="test verdict",
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


async def _mock_session_gen():
    session = AsyncMock()
    session.get = AsyncMock(return_value=MagicMock())
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    yield session


def _mk_session():
    return _mock_session_gen()


@pytest.mark.asyncio
async def test_run_single_symbol_success(monkeypatch):
    job_id = uuid.uuid4()
    monkeypatch.setattr("app.batch._supervisor.run_analysis", AsyncMock(return_value=_mock_verdict()))
    monkeypatch.setattr("app.batch.get_session", _mk_session)
    monkeypatch.setattr("app.batch.batch_symbols_counter", MagicMock())

    import asyncio
    sem = asyncio.Semaphore(5)
    await _run_single_symbol(sem, "AAPL", job_id, 10_000.0, 2.0)


@pytest.mark.asyncio
async def test_run_single_symbol_failure(monkeypatch):
    job_id = uuid.uuid4()
    monkeypatch.setattr(
        "app.batch._supervisor.run_analysis", AsyncMock(side_effect=RuntimeError("crash"))
    )
    monkeypatch.setattr("app.batch.get_session", _mk_session)
    monkeypatch.setattr("app.batch.batch_symbols_counter", MagicMock())

    import asyncio
    sem = asyncio.Semaphore(5)
    await _run_single_symbol(sem, "AAPL", job_id, None, None)


@pytest.mark.asyncio
async def test_increment_counter(monkeypatch):
    monkeypatch.setattr("app.batch.get_session", _mk_session)
    job_id = uuid.uuid4()
    await _increment_counter(job_id, "completed_symbols")


@pytest.mark.asyncio
async def test_run_batch_job_completes(monkeypatch):
    job_id = uuid.uuid4()
    monkeypatch.setattr("app.batch._supervisor.run_analysis", AsyncMock(return_value=_mock_verdict()))
    monkeypatch.setattr("app.batch.get_session", _mk_session)
    monkeypatch.setattr("app.batch.batch_symbols_counter", MagicMock())
    monkeypatch.setattr("app.batch.correlation_id_var", MagicMock())

    await run_batch_job(job_id, ["AAPL", "MSFT"], 10_000.0, 2.0, "test-corr-id")


@pytest.mark.asyncio
async def test_run_batch_job_partial_failure(monkeypatch):
    """Batch continues even when one symbol's analysis raises."""
    job_id = uuid.uuid4()
    call_count = 0

    async def _sometimes_fail(req):
        nonlocal call_count
        call_count += 1
        if req.symbol == "TSLA":
            raise RuntimeError("tsla failed")
        return _mock_verdict()

    monkeypatch.setattr("app.batch._supervisor.run_analysis", _sometimes_fail)
    monkeypatch.setattr("app.batch.get_session", _mk_session)
    monkeypatch.setattr("app.batch.batch_symbols_counter", MagicMock())
    monkeypatch.setattr("app.batch.correlation_id_var", MagicMock())

    await run_batch_job(job_id, ["AAPL", "TSLA"], None, None, "")
    assert call_count == 2
