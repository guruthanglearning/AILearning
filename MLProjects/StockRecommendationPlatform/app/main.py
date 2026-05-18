from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import date

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import select

from app.batch import run_batch_job
from app.config import settings
from app.db.models import BatchJob
from app.db.session import get_session, init_engine
from app.limiter import limiter
from app.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from app.observability import (
    configure_logging,
    configure_otel,
    create_instrumentator,
    get_correlation_id,
)
from app.routers import alerts as alerts_router
from app.routers import auth as auth_router
from app.routers import watchlists as watchlists_router
from app.schemas.agents import AnalysisRunRequest, SupervisorVerdict
from app.schemas.batch import BatchJobRequest, BatchJobResponse, BatchJobStatus
from app.supervisor import Supervisor
from app.universe import COMPOSITION_AS_OF, TOP_10, TOP_100, get_sp500


def _parse_cors_origins(raw: str) -> list[str]:
    if raw.strip() == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_otel()
    init_engine()
    if settings.otel_enabled:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        from app.db.session import _engine  # type: ignore[attr-defined]
        SQLAlchemyInstrumentor().instrument(engine=_engine)
    yield


app = FastAPI(
    title="Stock Recommendation Platform",
    description="Multi-agent research pipeline with decision aids (not investment advice).",
    version="0.3.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Registered first = innermost = last to see request (Starlette LIFO)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(CorrelationIdMiddleware)
# Registered last = outermost = security headers on ALL responses including 429/404
app.add_middleware(SecurityHeadersMiddleware)

if settings.metrics_enabled:
    _instrumentator = create_instrumentator()
    _instrumentator.instrument(app)
    _instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
    if settings.otel_enabled:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)

app.include_router(auth_router.router, prefix="/v1/auth/keys", tags=["auth"])
app.include_router(watchlists_router.router, prefix="/v1/watchlists", tags=["watchlists"])
app.include_router(alerts_router.router, prefix="/v1/alerts", tags=["alerts"])

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
@limiter.limit(settings.rate_limit_analysis)
async def run_analysis(request: Request, req: AnalysisRunRequest) -> SupervisorVerdict:
    """Run all specialist agents + supervisor; includes decision_aids for stock vs options.
    Hypothetical research only — not investment advice."""
    return await _supervisor.run_analysis(req)


@app.get("/v1/analysis/run/{symbol}", response_model=SupervisorVerdict)
@limiter.limit(settings.rate_limit_analysis)
async def run_analysis_get(
    request: Request,
    symbol: str,
    portfolio_value_usd: float | None = None,
    max_risk_per_trade_pct: float | None = None,
) -> SupervisorVerdict:
    """GET convenience wrapper for quick testing. Hypothetical research only — not investment advice."""
    return await _supervisor.run_analysis(
        AnalysisRunRequest(
            symbol=symbol,
            portfolio_value_usd=portfolio_value_usd,
            max_risk_per_trade_pct=max_risk_per_trade_pct,
        )
    )


@app.post("/v1/analysis/batch", response_model=BatchJobResponse, status_code=202)
@limiter.limit(settings.rate_limit_batch)
async def start_batch(
    request: Request,
    req: BatchJobRequest,
    background_tasks: BackgroundTasks,
) -> BatchJobResponse:
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
        get_correlation_id(),
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
@limiter.limit(settings.rate_limit_default)
async def get_batch_status(request: Request, job_id: uuid.UUID) -> BatchJobResponse:
    """Poll batch job status and counters."""
    async for session in get_session():
        row = await session.get(BatchJob, job_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Batch job not found")
        return _batch_row_to_response(row)
