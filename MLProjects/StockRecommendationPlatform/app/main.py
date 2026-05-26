from __future__ import annotations

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from functools import partial

import structlog
import yfinance as yf
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import select

from app.batch import run_batch_job
from app.config import settings
from app.db.models import AnalysisRun, BatchJob
from app.db.session import get_session, init_engine
from app.ingest import warm_cache
from app.limiter import limiter
from app.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from app.observability import (
    configure_logging,
    configure_otel,
    create_instrumentator,
    get_correlation_id,
)
from app.providers.factory import build_provider
from app.routers import alerts as alerts_router
from app.routers import auth as auth_router
from app.routers import watchlists as watchlists_router
from app.schemas.agents import (
    AnalysisHistoryItem,
    AnalysisRunRequest,
    LiveQuote,
    MarketQuoteRow,
    SupervisorVerdict,
)
from app.schemas.batch import BatchJobRequest, BatchJobResponse, BatchJobStatus
from app.supervisor import Supervisor
from app.universe import COMPOSITION_AS_OF, TOP_10, TOP_100, get_sp500

log = structlog.get_logger(__name__)


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


@app.get("/v1/analysis/stream/{symbol}")
@limiter.limit(settings.rate_limit_analysis)
async def stream_analysis_sse(
    request: Request,
    symbol: str,
    portfolio_value_usd: float | None = None,
    max_risk_per_trade_pct: float | None = None,
) -> StreamingResponse:
    """SSE stream: yields agent_done events as each agent completes, then the full verdict."""
    req = AnalysisRunRequest(
        symbol=symbol,
        portfolio_value_usd=portfolio_value_usd,
        max_risk_per_trade_pct=max_risk_per_trade_pct,
    )

    async def _generate():
        try:
            async for event in _supervisor.stream_analysis(req):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            log.warning("stream_analysis_error", error=str(exc))
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/v1/quote/live/{symbol}", response_model=LiveQuote)
@limiter.limit("30/minute")
async def get_live_quote(request: Request, symbol: str) -> LiveQuote:
    """Lightweight live quote: pre-market, open, current, post-market prices."""
    sym = symbol.upper().strip()

    def _fetch() -> dict:
        info = yf.Ticker(sym).info or {}
        current = info.get("regularMarketPrice") or info.get("currentPrice")
        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
        change_pct = None
        if current and prev_close and prev_close > 0:
            change_pct = (current - prev_close) / prev_close * 100
        return {
            "pre_market":     info.get("preMarketPrice"),
            "open_price":     info.get("regularMarketOpen") or info.get("open"),
            "current":        current,
            "post_market":    info.get("postMarketPrice"),
            "previous_close": prev_close,
            "day_change_pct": change_pct,
            "volume":         info.get("regularMarketVolume") or info.get("volume"),
            "market_state":   info.get("marketState"),
        }

    try:
        data = await asyncio.get_event_loop().run_in_executor(None, partial(_fetch))
        return LiveQuote(symbol=sym, **data)
    except Exception:
        return LiveQuote(symbol=sym)


@app.get("/v1/market/quotes", response_model=list[MarketQuoteRow])
@limiter.limit("120/minute")
async def get_market_quotes(
    request: Request,
    symbols: str = Query(..., description="Comma-separated symbols, max 50"),
) -> list[MarketQuoteRow]:
    """Batch quote fetch for the market-grid UI. Returns live data for up to 50 symbols."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return []
    if len(sym_list) > 50:
        raise HTTPException(status_code=422, detail="Maximum 50 symbols per request")

    def _fetch_one(sym: str) -> MarketQuoteRow:
        try:
            info = yf.Ticker(sym).info or {}
            now = datetime.now(tz=UTC)
            current = info.get("regularMarketPrice") or info.get("currentPrice")
            prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
            raw_change = info.get("regularMarketChange")
            raw_chg_pct = info.get("regularMarketChangePercent")
            if raw_change is None and current and prev_close and prev_close > 0:
                raw_change = current - prev_close
            if raw_chg_pct is None and raw_change and prev_close and prev_close > 0:
                raw_chg_pct = (raw_change / prev_close) * 100
            return MarketQuoteRow(
                symbol=sym,
                pre_mkt_change_pct=info.get("preMarketChangePercent"),
                pre_mkt_price=info.get("preMarketPrice"),
                last_price=current,
                change=raw_change,
                post_mkt_change_pct=info.get("postMarketChangePercent"),
                post_mkt_price=info.get("postMarketPrice"),
                market_cap=info.get("marketCap"),
                exchange=info.get("exchange"),
                week_52_high=info.get("fiftyTwoWeekHigh"),
                week_52_low=info.get("fiftyTwoWeekLow"),
                shares_outstanding=info.get("sharesOutstanding"),
                volume=info.get("regularMarketVolume") or info.get("volume"),
                change_pct=raw_chg_pct,
                fetched_at_utc=now,
            )
        except Exception:
            return MarketQuoteRow(symbol=sym, fetched_at_utc=datetime.now(tz=UTC))

    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, _fetch_one, s) for s in sym_list]
    results = await asyncio.gather(*tasks)
    return list(results)


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


@app.get("/v1/analysis/history/{symbol}", response_model=list[AnalysisHistoryItem])
@limiter.limit(settings.rate_limit_default)
async def get_analysis_history(
    request: Request,
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[AnalysisHistoryItem]:
    """Return the N most recent completed analysis runs for a symbol."""
    sym = symbol.upper().strip()
    async for session in get_session():
        result = await session.execute(
            select(AnalysisRun)
            .where(AnalysisRun.symbol == sym, AnalysisRun.status == "complete")
            .order_by(AnalysisRun.started_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        items: list[AnalysisHistoryItem] = []
        for row in rows:
            score: float | None = None
            if row.verdict_json:
                try:
                    score = row.verdict_json["decision_aids"]["stock_vs_options_score"]
                except (KeyError, TypeError):
                    pass
            items.append(
                AnalysisHistoryItem(
                    run_id=row.id,
                    symbol=row.symbol,
                    started_at=row.started_at,
                    finished_at=row.finished_at,
                    instrument_recommendation=row.instrument_recommendation,
                    confidence_note=row.confidence_note,
                    last_price=row.last_price,
                    stock_vs_options_score=score,
                    status=row.status,
                )
            )
        return items


@app.post("/v1/ingest/warm", status_code=202)
@limiter.limit("10/minute")
async def trigger_ingest_warm(
    request: Request,
    background_tasks: BackgroundTasks,
    symbols: list[str],
) -> dict[str, str]:
    """Warm Redis cache for specified symbols. No-op when USE_REDIS=false."""
    cleaned = [s.upper().strip() for s in symbols if s.strip()]
    if settings.use_redis and cleaned:
        background_tasks.add_task(warm_cache, cleaned, build_provider())
    return {"status": "queued", "count": str(len(cleaned))}
