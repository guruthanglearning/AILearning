from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import date

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.batch import run_batch_job
from app.db.models import BatchJob
from app.db.session import get_session, init_engine
from app.schemas.agents import AnalysisRunRequest, SupervisorVerdict
from app.schemas.batch import BatchJobRequest, BatchJobResponse, BatchJobStatus
from app.supervisor import Supervisor
from app.universe import COMPOSITION_AS_OF, TOP_10, TOP_100, get_sp500


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    yield


app = FastAPI(
    title="Stock Recommendation Platform",
    description="Multi-agent research pipeline with decision aids (not investment advice).",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_supervisor = Supervisor()


def _resolve_universe(req: BatchJobRequest) -> list[str]:
    if req.universe == "top10":
        return list(TOP_10)
    if req.universe == "top100":
        return list(TOP_100)
    if req.universe == "full":
        return get_sp500()
    if req.universe == "custom":
        if not req.symbols:
            raise HTTPException(status_code=422, detail="symbols required when universe=custom")
        return [s.upper().strip() for s in req.symbols]
    raise HTTPException(status_code=422, detail=f"Unknown universe: {req.universe!r}")


def _batch_row_to_response(row: BatchJob) -> BatchJobResponse:
    return BatchJobResponse(
        job_id=row.id,
        status=BatchJobStatus(row.status),
        universe=row.universe,
        total_symbols=row.total_symbols,
        completed_symbols=row.completed_symbols,
        failed_symbols=row.failed_symbols,
        composition_as_of=row.composition_as_of.isoformat() if row.composition_as_of else None,
        requested_at=row.requested_at,
        finished_at=row.finished_at,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/analysis/run", response_model=SupervisorVerdict)
async def run_analysis(req: AnalysisRunRequest) -> SupervisorVerdict:
    """Run all specialist agents + supervisor; includes decision_aids for stock vs options."""
    return await _supervisor.run_analysis(req)


@app.get("/v1/analysis/run/{symbol}", response_model=SupervisorVerdict)
async def run_analysis_get(
    symbol: str,
    portfolio_value_usd: float | None = None,
    max_risk_per_trade_pct: float | None = None,
) -> SupervisorVerdict:
    """GET convenience wrapper for quick testing."""
    return await _supervisor.run_analysis(
        AnalysisRunRequest(
            symbol=symbol,
            portfolio_value_usd=portfolio_value_usd,
            max_risk_per_trade_pct=max_risk_per_trade_pct,
        )
    )


@app.post("/v1/analysis/batch", response_model=BatchJobResponse, status_code=202)
async def start_batch(req: BatchJobRequest, background_tasks: BackgroundTasks) -> BatchJobResponse:
    """Submit a batch analysis job across a universe slice. Returns immediately with job_id."""
    # Idempotency: re-submit with same batch_key returns existing non-failed job
    if req.batch_key:
        async for session in get_session():
            result = await session.execute(
                select(BatchJob).where(BatchJob.batch_key == req.batch_key)
            )
            existing = result.scalar_one_or_none()
            if existing is not None and existing.status != "failed":
                return _batch_row_to_response(existing)

    symbols = _resolve_universe(req)
    job_id = uuid.uuid4()

    async for session in get_session():
        job = BatchJob(
            id=job_id,
            status="pending",
            universe=req.universe,
            total_symbols=len(symbols),
            batch_key=req.batch_key,
            symbols_json=symbols,
            composition_as_of=date.fromisoformat(COMPOSITION_AS_OF),
        )
        session.add(job)
        await session.commit()

    background_tasks.add_task(
        run_batch_job,
        job_id,
        symbols,
        req.portfolio_value_usd,
        req.max_risk_per_trade_pct,
    )

    return BatchJobResponse(
        job_id=job_id,
        status=BatchJobStatus.pending,
        universe=req.universe,
        total_symbols=len(symbols),
        completed_symbols=0,
        failed_symbols=0,
        composition_as_of=COMPOSITION_AS_OF,
    )


@app.get("/v1/analysis/batch/{job_id}", response_model=BatchJobResponse)
async def get_batch_status(job_id: uuid.UUID) -> BatchJobResponse:
    """Poll batch job status and counters."""
    async for session in get_session():
        row = await session.get(BatchJob, job_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Batch job not found")
        return _batch_row_to_response(row)
