from __future__ import annotations

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import pandas as pd
import structlog
import yfinance as yf
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import select

import app.error_log as error_log
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
    MomentumSectorsResponse,
    MomentumStockRow,
    SectorMomentum,
    SupervisorVerdict,
)
from app.schemas.batch import BatchJobRequest, BatchJobResponse, BatchJobStatus
from app.services.claude_service import CLAUDE_MODELS, ClaudeServiceError, get_session_usage
from app.supervisor import Supervisor
from app.universe import COMPOSITION_AS_OF, TOP_10, TOP_100, get_sp500

log = structlog.get_logger(__name__)

# ── Simple TTL cache for expensive provider lookups ───────────────────────────
_TTL_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SECS = 300        # 5 minutes (default: peers, momentum)
_PRICE_HISTORY_TTL_SECS = 60  # 1 minute (price charts — fresher data per analysis)


def _cache_get(key: str, ttl: float = _CACHE_TTL_SECS) -> Any | None:
    entry = _TTL_CACHE.get(key)
    if entry and time.monotonic() - entry[0] < ttl:
        return entry[1]
    _TTL_CACHE.pop(key, None)
    return None


def _cache_set(key: str, value: Any) -> None:
    _TTL_CACHE[key] = (time.monotonic(), value)


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
    if settings.polygon_api_key:
        from app.polygon_ws import init_ws_manager
        init_ws_manager(settings.polygon_api_key)
    yield


app = FastAPI(
    title="Stock Recommendation Platform",
    description="Multi-agent research pipeline with decision aids (not investment advice).",
    version="0.3.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


async def _claude_service_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.add_exception_handler(ClaudeServiceError, _claude_service_error_handler)

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
    """Live quote via configured provider (Polygon when API key is set, yfinance otherwise)."""
    sym = symbol.upper().strip()
    provider = build_provider()
    try:
        data = await provider.get_quote(sym)
        return LiveQuote(
            symbol=sym,
            open_price=data.get("open_price"),
            current=data.get("last_price"),
            previous_close=data.get("previous_close"),
            day_change_pct=data.get("day_change_pct"),
            volume=data.get("volume"),
            market_state=data.get("market_state"),
        )
    except Exception:
        return LiveQuote(symbol=sym)


@app.websocket("/v1/ws/quote/{symbol}")
async def ws_live_quote(websocket: WebSocket, symbol: str) -> None:
    """Real-time per-second price updates via Polygon WebSocket relay.
    Closes with 1013 (Try Again Later) when Polygon is not configured."""
    if not settings.polygon_api_key:
        await websocket.close(code=1013, reason="Polygon API key not configured")
        return
    from app.polygon_ws import get_ws_manager
    manager = get_ws_manager()
    if manager is None:
        await websocket.close(code=1013, reason="WS manager not initialised")
        return
    sym = symbol.upper().strip()
    await websocket.accept()
    await manager.subscribe(sym, websocket)
    try:
        while True:
            await websocket.receive_text()   # discard client pings; keeps conn alive
    except WebSocketDisconnect:
        pass
    finally:
        await manager.unsubscribe(sym, websocket)


@app.websocket("/v1/ws/market-grid")
async def ws_market_grid(
    websocket: WebSocket,
    symbols: str = Query(default=""),
) -> None:
    """Real-time price updates for multiple symbols in one WebSocket connection.

    Subscribes the client to all requested symbols via the Polygon relay.
    Each price event has the same shape as /v1/ws/quote/{symbol}.
    Requires POLYGON_API_KEY (Starter plan = 15-min delayed feed).
    """
    if not settings.polygon_api_key:
        await websocket.close(code=1013, reason="Polygon API key not configured")
        return
    from app.polygon_ws import get_ws_manager
    manager = get_ws_manager()
    if manager is None:
        await websocket.close(code=1013, reason="WS manager not initialised")
        return
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        await websocket.close(code=1008, reason="No symbols provided")
        return
    await websocket.accept()
    for sym in sym_list:
        await manager.subscribe(sym, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        for sym in sym_list:
            await manager.unsubscribe(sym, websocket)


@app.get("/v1/market/quotes", response_model=list[MarketQuoteRow])
@limiter.limit("120/minute")
async def get_market_quotes(
    request: Request,
    symbols: str = Query(..., description="Comma-separated symbols, max 50"),
) -> list[MarketQuoteRow]:
    """Batch quote fetch for the market-grid UI.

    Prices come from Polygon batch snapshot (reliable, one API call).
    Supplementary fields (earnings, dividends, 52-wk, market cap) come from yfinance.
    """
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return []
    if len(sym_list) > 50:
        raise HTTPException(status_code=422, detail="Maximum 50 symbols per request")

    # ── Step 1: Polygon batch snapshot for reliable price data ────────────────
    polygon_prices: dict[str, dict] = {}
    if settings.polygon_api_key:
        try:
            from app.providers.polygon_provider import PolygonProvider
            _poly = PolygonProvider(api_key=settings.polygon_api_key)
            raw = await _poly._get(
                "/v2/snapshot/locale/us/markets/stocks/tickers",
                tickers=",".join(sym_list),
            )
            for t in raw.get("tickers") or []:
                sym = t.get("ticker", "")
                day  = t.get("day") or {}
                lt   = t.get("lastTrade") or {}
                prev = t.get("prevDay") or {}
                polygon_prices[sym] = {
                    "last_price": lt.get("p") or day.get("c"),
                    "change":     t.get("todaysChange"),
                    "prev_close": prev.get("c"),
                }
            await _poly.aclose()
        except Exception:
            pass  # fall through to yfinance prices below

    # ── Step 2: yfinance for supplementary fields Polygon doesn't carry ───────
    def _fetch_supplementary(sym: str) -> dict:
        try:
            info = yf.Ticker(sym).info or {}
            earnings_date: str | None = None
            for key in ("earningsTimestamp", "earningsDate"):
                val = info.get(key)
                if val is None:
                    continue
                ts = val[0] if isinstance(val, list) else val
                if isinstance(ts, (int, float)) and ts > 0:
                    earnings_date = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y/%m/%d")
                    break
            div_payment_date: str | None = None
            dd = info.get("dividendDate")
            if isinstance(dd, (int, float)) and dd > 0:
                div_payment_date = datetime.fromtimestamp(dd, tz=UTC).strftime("%Y-%m-%d")
            yf_price = info.get("regularMarketPrice") or info.get("currentPrice")
            yf_prev  = info.get("regularMarketPreviousClose") or info.get("previousClose")
            yf_chg   = info.get("regularMarketChange")
            if yf_chg is None and yf_price and yf_prev and yf_prev > 0:
                yf_chg = yf_price - yf_prev
            return {
                "yf_last_price":   yf_price,
                "yf_change":       yf_chg,
                "pre_mkt_price":   info.get("preMarketPrice"),
                "pre_mkt_change":  info.get("preMarketChange"),
                "post_mkt_price":  info.get("postMarketPrice"),
                "post_mkt_change": info.get("postMarketChange"),
                "earnings_date":   earnings_date,
                "market_cap":      info.get("marketCap"),
                "div_payment_date": div_payment_date,
                "exchange":        info.get("exchange"),
                "week_52_high":    info.get("fiftyTwoWeekHigh"),
                "week_52_low":     info.get("fiftyTwoWeekLow"),
                "shares_outstanding": info.get("sharesOutstanding"),
            }
        except Exception:
            return {}

    loop = asyncio.get_event_loop()
    supp_tasks = [loop.run_in_executor(None, _fetch_supplementary, s) for s in sym_list]
    supp_list  = await asyncio.gather(*supp_tasks)
    supp_map   = {sym: data for sym, data in zip(sym_list, supp_list)}

    # ── Step 3: Merge — Polygon prices take priority over yfinance ────────────
    now = datetime.now(tz=UTC)
    results = []
    for sym in sym_list:
        poly = polygon_prices.get(sym, {})
        supp = supp_map.get(sym, {})
        results.append(MarketQuoteRow(
            symbol=sym,
            last_price=poly.get("last_price") or supp.get("yf_last_price"),
            change=poly.get("change") or supp.get("yf_change"),
            pre_mkt_price=supp.get("pre_mkt_price"),
            pre_mkt_change=supp.get("pre_mkt_change"),
            post_mkt_price=supp.get("post_mkt_price"),
            post_mkt_change=supp.get("post_mkt_change"),
            earnings_date=supp.get("earnings_date"),
            market_cap=supp.get("market_cap"),
            div_payment_date=supp.get("div_payment_date"),
            exchange=supp.get("exchange"),
            week_52_high=supp.get("week_52_high"),
            week_52_low=supp.get("week_52_low"),
            shares_outstanding=supp.get("shares_outstanding"),
            fetched_at_utc=now,
        ))
    return results


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


@app.get("/v1/price-history/{symbol}")
@limiter.limit(settings.rate_limit_default)
async def get_price_history(
    request: Request,
    symbol: str,
    period: str = Query(default="3mo", pattern="^(1mo|3mo|6mo|1y)$"),
) -> dict:
    """OHLCV price history for a symbol, used by the mini price chart."""
    sym = symbol.upper().strip()
    cache_key = f"price_history:{sym}:{period}"
    cached = _cache_get(cache_key, ttl=_PRICE_HISTORY_TTL_SECS)
    if cached is not None:
        return cached

    provider = build_provider()
    try:
        hist = await provider.get_price_history(sym, period)
    except Exception as exc:
        raise HTTPException(500, f"Price history fetch failed: {exc}") from exc
    if hist is None or hist.empty:
        raise HTTPException(404, "No price history data available")
    hist = hist.reset_index()
    date_col = "Date" if "Date" in hist.columns else hist.columns[0]
    records = []
    for _, row in hist.iterrows():
        records.append({
            "date": str(row[date_col])[:10],
            "open":  round(float(row["Open"]),  2) if "Open"  in hist.columns else None,
            "high":  round(float(row["High"]),  2) if "High"  in hist.columns else None,
            "low":   round(float(row["Low"]),   2) if "Low"   in hist.columns else None,
            "close": round(float(row["Close"]), 2) if "Close" in hist.columns else None,
            "volume": int(row["Volume"])           if "Volume" in hist.columns else None,
        })
    result = {"symbol": sym, "period": period, "data": records}
    _cache_set(cache_key, result)
    return result


# Hardcoded sector → representative peer tickers (top liquid names per sector)
_SECTOR_PEERS: dict[str, list[str]] = {
    "Technology":             ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
    "Consumer Cyclical":      ["AMZN", "TSLA", "HD", "NKE", "SBUX"],
    "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "T"],
    "Healthcare":             ["JNJ", "UNH", "PFE", "ABBV", "MRK"],
    "Financials":             ["JPM", "BAC", "WFC", "GS", "MS"],
    "Industrials":            ["CAT", "BA", "HON", "UPS", "RTX"],
    "Consumer Defensive":     ["PG", "KO", "PEP", "WMT", "COST"],
    "Energy":                 ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Basic Materials":        ["LIN", "APD", "ECL", "NEM", "FCX"],
    "Real Estate":            ["AMT", "PLD", "CCI", "EQIX", "SPG"],
    "Utilities":              ["NEE", "DUK", "SO", "D", "AEP"],
}


@app.get("/v1/peers/{symbol}")
@limiter.limit(settings.rate_limit_default)
async def get_peers(request: Request, symbol: str) -> dict:
    """Return sector peer comparison data (PE, market cap, YTD return)."""
    sym = symbol.upper().strip()
    cache_key = f"peers:{sym}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    loop = asyncio.get_event_loop()

    def _fetch_one(t: str) -> dict:
        try:
            ticker = yf.Ticker(t)
            info = ticker.info
            hist = ticker.history(period="ytd")
            ytd_return = None
            if not hist.empty and len(hist) >= 2:
                ytd_return = round((hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100, 2)
            return {
                "symbol":     t,
                "name":       info.get("shortName") or info.get("longName") or t,
                "price":      info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio":   info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "ytd_return": ytd_return,
                "sector":     info.get("sector"),
            }
        except Exception:
            return {"symbol": t, "name": t}

    def _get_sector_and_peers() -> tuple[str | None, list[str]]:
        try:
            info = yf.Ticker(sym).info
            sector = info.get("sector")
            peers = _SECTOR_PEERS.get(sector or "", [])
            all_tickers = [sym] + [p for p in peers if p != sym]
            return sector, all_tickers[:5]
        except Exception:
            return None, [sym]

    sector, tickers = await loop.run_in_executor(None, _get_sector_and_peers)
    # Fetch all tickers in parallel instead of sequentially
    tasks = [loop.run_in_executor(None, _fetch_one, t) for t in tickers]
    peers_data = list(await asyncio.gather(*tasks))
    result = {"symbol": sym, "sector": sector, "peers": peers_data}
    _cache_set(cache_key, result)
    return result


@app.get("/v1/logs/errors")
@limiter.limit(settings.rate_limit_default)
async def get_error_logs(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
) -> list[dict]:
    """Return recent agent error log entries (in-memory ring buffer, last 500)."""
    return error_log.get_recent(limit)


@app.delete("/v1/logs/errors", status_code=204)
@limiter.limit("10/minute")
async def clear_error_logs(request: Request) -> None:
    """Clear the in-memory error log buffer."""
    error_log.clear()


@app.get("/v1/claude/models")
async def list_claude_models():
    """Return available Claude model options with pricing metadata."""
    return {"models": CLAUDE_MODELS}


@app.get("/v1/claude/usage")
async def get_claude_usage():
    """Return cumulative token usage and estimated cost for this server session."""
    return get_session_usage()


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


# ── Momentum Sectors ──────────────────────────────────────────────────────────

# Ensures only one concurrent yfinance fetch runs when the cache is cold,
# preventing thundering-herd from multiple simultaneous browser tabs.
_MOMENTUM_FETCH_LOCK = asyncio.Lock()

_MOMENTUM_UNIVERSE: dict[str, list[str]] = {
    "Technology":             ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "ADBE", "CRM", "AMD", "QCOM", "TXN"],
    "Consumer Cyclical":      ["AMZN", "TSLA", "HD", "LOW", "NKE", "SBUX", "TJX", "MCD", "BKNG", "F"],
    "Communication Services": ["GOOGL", "META", "NFLX", "DIS", "T", "VZ", "CMCSA", "CHTR", "SNAP", "PINS"],
    "Healthcare":             ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY"],
    "Financials":             ["JPM", "BAC", "WFC", "GS", "MS", "AXP", "BLK", "SCHW", "USB", "C"],
    "Industrials":            ["CAT", "BA", "HON", "UPS", "RTX", "GE", "MMM", "DE", "FDX", "LMT"],
    "Consumer Defensive":     ["WMT", "PG", "KO", "PEP", "COST", "MDLZ", "MO", "PM", "CL", "EL"],
    "Energy":                 ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
    "Basic Materials":        ["LIN", "APD", "ECL", "NEM", "FCX", "DOW", "DD", "ALB", "CF", "MOS"],
    "Real Estate":            ["AMT", "PLD", "CCI", "EQIX", "SPG", "DLR", "PSA", "O", "WELL", "AVB"],
    "Utilities":              ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PCG", "XEL", "ES"],
}


# ── Professional momentum helpers ─────────────────────────────────────────────

def _rsi(closes: pd.Series, period: int = 14) -> float | None:
    """Wilder's 14-day RSI from a daily close series."""
    s = closes.dropna()
    if len(s) < period + 1:
        return None
    delta = s.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    last_loss = float(loss.iloc[-1])
    if last_loss == 0:
        return 100.0
    rs = float(gain.iloc[-1]) / last_loss
    return round(100.0 - 100.0 / (1.0 + rs), 1)


def _stock_returns(s: pd.Series) -> tuple[float | None, float | None, float | None]:
    """(1M, 3M, 6M) returns from a daily close series (21/63/126 trading days)."""
    s = s.dropna()
    if len(s) < 5:
        return None, None, None
    now = float(s.iloc[-1])

    def _ret(n: int) -> float | None:
        if len(s) < n + 1:
            return None
        past = float(s.iloc[-n])
        return (now / past - 1.0) if past > 0 else None

    return _ret(21), _ret(63), _ret(min(126, len(s) - 1))


def _fetch_universe_history() -> pd.DataFrame | None:
    """Single batch yf.download for all universe stocks + SPY benchmark."""
    all_syms = [s for syms in _MOMENTUM_UNIVERSE.values() for s in syms]
    to_fetch = list(dict.fromkeys(all_syms + ["SPY"]))
    try:
        raw = yf.download(
            to_fetch,
            period="6mo",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if isinstance(raw.columns, pd.MultiIndex):
            return raw["Close"]
        # Single-ticker fallback (shouldn't happen with 100+ tickers)
        return raw.rename(columns={"Close": to_fetch[0]})[["Close"]].rename(
            columns={"Close": to_fetch[0]}
        )
    except Exception:
        return None


def _percentile_ranks(values: list[float | None]) -> list[float | None]:
    """Cross-sectional percentile rank (0–100) within the non-null values."""
    indexed = [(i, v) for i, v in enumerate(values) if v is not None]
    if not indexed:
        return [None] * len(values)
    ranked = sorted(indexed, key=lambda x: x[1])
    n = len(ranked)
    rank_map: dict[int, float] = {
        i: (r / (n - 1)) * 100.0 if n > 1 else 50.0
        for r, (i, _) in enumerate(ranked)
    }
    return [rank_map.get(i) for i in range(len(values))]


def _compute_momentum_score_pro(
    pct_6m: float | None,
    pct_3m: float | None,
    pct_1m: float | None,
    pct_vs_spy: float | None,
    rsi_14: float | None,
    price: float | None,
    sma50: float | None,
    sma200: float | None,
    low52: float | None,
    high52: float | None,
) -> float | None:
    """
    Cross-sectional momentum score (0–100).

    Weights (research-backed):
      - 6M return percentile rank   30 pts  (Jegadeesh-Titman primary signal)
      - 3M return percentile rank   20 pts  (intermediate momentum)
      - vs-SPY 6M percentile rank   20 pts  (relative alpha vs benchmark)
      - 1M return percentile rank   10 pts  (skip-1M adjustment is applied at caller)
      - SMA trend alignment         12 pts  (price > SMA200: 6 pts; golden cross: +6)
      - 52-week range position       8 pts  (proximity to new highs)
    RSI quality filter: -5 pts if RSI > 80 or < 30 (extreme overbought/oversold).
    """
    if price is None:
        return None

    # ── Cross-sectional component (80 pts max) ──────────────────────────────
    cross, total_w = 0.0, 0.0
    for pct, w in [
        (pct_6m,    0.375),   # 30 pts
        (pct_3m,    0.250),   # 20 pts
        (pct_vs_spy, 0.250),  # 20 pts
        (pct_1m,    0.125),   # 10 pts
    ]:
        if pct is not None:
            cross += pct * w
            total_w += w

    if total_w > 0:
        cross_score = (cross / total_w) * 0.80   # normalise to 80 pts
    elif low52 is not None and high52 is not None and high52 > low52:
        # Graceful fallback when no history data: use 52W position scaled to 40 pts
        cross_score = ((price - low52) / (high52 - low52)) * 40.0
    else:
        return None

    # ── Trend alignment (12 pts) ─────────────────────────────────────────────
    trend = 0.0
    if sma200 is not None and price > sma200:
        trend += 6.0
        if sma50 is not None and price > sma50 and sma50 > sma200:
            trend += 6.0   # golden cross: both SMAs confirm uptrend

    # ── 52-week high proximity (8 pts) ──────────────────────────────────────
    range_pts = 0.0
    if low52 is not None and high52 is not None and high52 > low52:
        range_pts = ((price - low52) / (high52 - low52)) * 8.0

    # ── RSI quality filter ───────────────────────────────────────────────────
    rsi_adj = 0.0
    if rsi_14 is not None:
        if rsi_14 > 80 or rsi_14 < 30:
            rsi_adj = -5.0   # overbought / oversold penalty

    raw = cross_score + trend + range_pts + rsi_adj
    return round(min(100.0, max(0.0, raw)), 1)


def _fetch_stock_raw(sym: str) -> dict:
    """Fetch yfinance .info for one symbol; returns a plain dict for downstream scoring."""
    try:
        info = yf.Ticker(sym).info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        return {
            "symbol": sym,
            "company_name": info.get("shortName") or info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "pre_market": info.get("preMarketPrice"),
            "open_price": info.get("regularMarketOpen"),
            "close_price": price,
            "post_market": info.get("postMarketPrice"),
            "day_change_pct": info.get("regularMarketChangePercent"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "sma50": info.get("fiftyDayAverage"),
            "sma200": info.get("twoHundredDayAverage"),
            "market_cap": info.get("marketCap"),
        }
    except Exception:
        return {"symbol": sym}


@app.get("/v1/momentum/sectors", response_model=MomentumSectorsResponse)
@limiter.limit("30/minute")
async def get_momentum_sectors(
    request: Request,
    limit: int = Query(default=10, ge=1, le=25),
) -> MomentumSectorsResponse:
    """Top-N momentum stocks per GICS sector.

    Professional cross-sectional scoring:
      - Multi-timeframe returns (1M/3M/6M) via single batch yf.download
      - Percentile-ranked within the 110-stock universe (relative, not absolute)
      - Relative strength vs SPY benchmark
      - SMA trend confirmation + 52-week high proximity
      - RSI quality filter for extreme overbought/oversold
    Not investment advice.
    """
    cache_key = "momentum_sectors_all"

    cached = _cache_get(cache_key)
    if cached is not None:
        all_sector_rows: list[tuple[str, list[MomentumStockRow]]] = cached["rows"]
        fetched_at: datetime = cached["fetched_at"]
    else:
        async with _MOMENTUM_FETCH_LOCK:
            cached = _cache_get(cache_key)
            if cached is not None:
                all_sector_rows = cached["rows"]
                fetched_at = cached["fetched_at"]
            else:
                loop = asyncio.get_event_loop()
                all_syms = [s for syms in _MOMENTUM_UNIVERSE.values() for s in syms]

                # ── Phase 1: batch history + per-symbol .info in parallel ──────
                hist_task = loop.run_in_executor(None, _fetch_universe_history)
                info_tasks = [loop.run_in_executor(None, _fetch_stock_raw, s) for s in all_syms]
                results = list(await asyncio.gather(hist_task, *info_tasks))
                close_df: pd.DataFrame | None = results[0]
                raw_data: list[dict] = results[1:]

                # ── Phase 2: compute returns + RSI from history ───────────────
                spy_6m: float | None = None
                hist_map: dict[str, dict] = {}

                if close_df is not None:
                    spy_series = close_df.get("SPY") if "SPY" in close_df.columns else None
                    if spy_series is not None:
                        _, _, spy_6m = _stock_returns(spy_series)

                    for sym in all_syms:
                        if sym in close_df.columns:
                            r1m, r3m, r6m = _stock_returns(close_df[sym])
                            vs_spy = (
                                (r6m - spy_6m)
                                if r6m is not None and spy_6m is not None
                                else None
                            )
                            hist_map[sym] = {
                                "return_1m": r1m,
                                "return_3m": r3m,
                                "return_6m": r6m,
                                "vs_spy_6m": vs_spy,
                                "rsi_14": _rsi(close_df[sym]),
                            }

                # ── Phase 3: cross-sectional percentile ranks ─────────────────
                r6m_vals   = [hist_map.get(d["symbol"], {}).get("return_6m")   for d in raw_data]
                r3m_vals   = [hist_map.get(d["symbol"], {}).get("return_3m")   for d in raw_data]
                r1m_vals   = [hist_map.get(d["symbol"], {}).get("return_1m")   for d in raw_data]
                spy_vals   = [hist_map.get(d["symbol"], {}).get("vs_spy_6m")   for d in raw_data]

                pct_6m  = _percentile_ranks(r6m_vals)
                pct_3m  = _percentile_ranks(r3m_vals)
                pct_1m  = _percentile_ranks(r1m_vals)
                pct_spy = _percentile_ranks(spy_vals)

                # ── Phase 4: build MomentumStockRow objects with final scores ──
                fetched: list[MomentumStockRow] = []
                for i, d in enumerate(raw_data):
                    sym = d["symbol"]
                    h = hist_map.get(sym, {})
                    score = _compute_momentum_score_pro(
                        pct_6m[i], pct_3m[i], pct_1m[i], pct_spy[i],
                        h.get("rsi_14"),
                        d.get("close_price"),
                        d.get("sma50"),
                        d.get("sma200"),
                        d.get("week_52_low"),
                        d.get("week_52_high"),
                    )
                    fetched.append(MomentumStockRow(
                        symbol=sym,
                        company_name=d.get("company_name"),
                        sector=d.get("sector"),
                        industry=d.get("industry"),
                        pre_market=d.get("pre_market"),
                        open_price=d.get("open_price"),
                        close_price=d.get("close_price"),
                        post_market=d.get("post_market"),
                        day_change_pct=d.get("day_change_pct"),
                        week_52_high=d.get("week_52_high"),
                        week_52_low=d.get("week_52_low"),
                        market_cap=d.get("market_cap"),
                        momentum_score=score,
                        return_1m=h.get("return_1m"),
                        return_3m=h.get("return_3m"),
                        return_6m=h.get("return_6m"),
                        vs_spy_6m=h.get("vs_spy_6m"),
                        rsi_14=h.get("rsi_14"),
                    ))

                # ── Phase 5: group by sector, sort by score, cache ────────────
                by_sym = {r.symbol: r for r in fetched}
                all_sector_rows = []
                for sector, syms in _MOMENTUM_UNIVERSE.items():
                    sector_rows = [by_sym[s] for s in syms if s in by_sym]
                    sector_rows.sort(
                        key=lambda r: r.momentum_score if r.momentum_score is not None else -1.0,
                        reverse=True,
                    )
                    all_sector_rows.append((sector, sector_rows))

                fetched_at = datetime.now(UTC)
                _cache_set(cache_key, {"rows": all_sector_rows, "fetched_at": fetched_at})

    sectors = [
        SectorMomentum(sector=sector, stocks=rows[:limit])
        for sector, rows in all_sector_rows
    ]
    return MomentumSectorsResponse(sectors=sectors, limit=limit, fetched_at_utc=fetched_at)
