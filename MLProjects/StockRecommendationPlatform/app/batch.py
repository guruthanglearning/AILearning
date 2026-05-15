"""Batch analysis engine — fan-out with concurrency limiter."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.config import settings
from app.db.models import BatchJob
from app.db.session import get_session
from app.schemas.agents import AnalysisRunRequest
from app.supervisor import Supervisor

log = logging.getLogger(__name__)

_supervisor = Supervisor()


async def run_batch_job(
    job_id: uuid.UUID,
    symbols: list[str],
    portfolio_value_usd: float | None,
    max_risk_per_trade_pct: float | None,
) -> None:
    async for session in get_session():
        row = await session.get(BatchJob, job_id)
        if row is not None:
            row.status = "running"
            row.started_at = datetime.now(tz=timezone.utc)
            await session.commit()

    sem = asyncio.Semaphore(settings.batch_concurrency)
    tasks = [
        _run_single_symbol(sem, sym, job_id, portfolio_value_usd, max_risk_per_trade_pct)
        for sym in symbols
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    async for session in get_session():
        row = await session.get(BatchJob, job_id)
        if row is not None:
            row.status = "complete" if row.failed_symbols == 0 else "partial"
            row.finished_at = datetime.now(tz=timezone.utc)
            await session.commit()


async def _run_single_symbol(
    sem: asyncio.Semaphore,
    symbol: str,
    job_id: uuid.UUID,
    portfolio_value_usd: float | None,
    max_risk_per_trade_pct: float | None,
) -> None:
    async with sem:
        try:
            req = AnalysisRunRequest(
                symbol=symbol,
                batch_job_id=job_id,
                portfolio_value_usd=portfolio_value_usd or 10_000.0,
                max_risk_per_trade_pct=max_risk_per_trade_pct or 2.0,
            )
            await _supervisor.run_analysis(req)
            await _increment_counter(job_id, "completed_symbols")
        except Exception as exc:
            log.warning("batch symbol %s failed: %s", symbol, exc)
            await _increment_counter(job_id, "failed_symbols")


async def _increment_counter(job_id: uuid.UUID, column: str) -> None:
    async for session in get_session():
        await session.execute(
            text(f"UPDATE batch_job SET {column} = {column} + 1 WHERE id = :id"),
            {"id": str(job_id)},
        )
        await session.commit()
