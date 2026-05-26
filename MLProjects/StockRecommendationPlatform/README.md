# Stock Recommendation Platform

A **production-oriented multi-agent research platform** that runs 7 specialist AI agents in parallel to analyse any US stock and return a structured **stock vs options** recommendation with full decision-support aids.

> **Not investment advice.** All outputs are hypothetical research tools only.

---

## Table of Contents

1. [Overview](#overview)
2. [Technical Architecture](#technical-architecture)
3. [System Design Workflow](#system-design-workflow)
4. [Agent Pipeline](#agent-pipeline)
5. [Database Schema](#database-schema)
6. [Frontend Pages](#frontend-pages)
7. [API Reference](#api-reference)
8. [Technology Stack](#technology-stack)
9. [Configuration](#configuration)
10. [Quick Start](#quick-start)
11. [Running Tests](#running-tests)
12. [Docker Setup](#docker-setup)
13. [Project Structure](#project-structure)

---

## Overview

The platform accepts a stock symbol (e.g. `AAPL`) and concurrently runs 7 specialist agents. A **Supervisor** merges their outputs into:

- `instrument_recommendation` — `stock | options | no_trade | insufficient_data`
- `confidence_note` — plain-English rationale
- `decision_aids` — checklist, volatility context, position sizing, instrument plays
- `options` — strategy family + strike guidance when options are favoured
- `technicals` — full snapshot (SMA/EMA/RSI/MACD/ATR/OBV/52-wk range)
- `agent_contributions` — per-agent status, headline, and expandable detail

Results are **streamed in real time** via SSE so each agent card lights up the moment that agent finishes — no waiting for the slowest agent.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT  (Browser)                                │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Analysis    │  │ Market Grid  │  │  Watchlists │  │   Alerts    │ │
│  │  (SSE live)  │  │ (auto-refresh│  │  & Symbols  │  │  & Triggers │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                 │                  │                │        │
│         └─────────────────┴──────────────────┴────────────────┘        │
│                           Next.js 14  (TypeScript)                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │  HTTP / SSE
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FASTAPI  BACKEND  (Python 3.12)                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Middleware Stack                                                │   │
│  │  SecurityHeaders → CorrelationId → SlowAPI(rate-limit) → CORS   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Routers                                                         │   │
│  │  /v1/analysis/run      POST  – blocking analysis                 │   │
│  │  /v1/analysis/stream   GET   – SSE streaming analysis            │   │
│  │  /v1/analysis/history  GET   – past runs for a symbol            │   │
│  │  /v1/market/quotes     GET   – batch live quotes (market grid)   │   │
│  │  /v1/analysis/batch    POST  – background batch across universe  │   │
│  │  /v1/watchlists        CRUD  – per-key watchlists + symbols      │   │
│  │  /v1/alerts            CRUD  – price / verdict change alerts     │   │
│  │  /v1/auth/keys         CRUD  – API key management                │   │
│  │  /v1/quote/live        GET   – lightweight live quote            │   │
│  │  /v1/ingest/warm       POST  – pre-warm Redis cache              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Supervisor                                                      │   │
│  │  asyncio.gather / asyncio.wait(FIRST_COMPLETED)                  │   │
│  │                                                                  │   │
│  │  ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐          │   │
│  │  │ Market  │ │Fundamentals│ │Technicals│ │Financials│          │   │
│  │  │  Data   │ │   Agent    │ │  Agent   │ │  Agent   │          │   │
│  │  └─────────┘ └────────────┘ └──────────┘ └──────────┘          │   │
│  │  ┌─────────┐ ┌────────────┐ ┌──────────┐                        │   │
│  │  │ Options │ │  RiskPro   │ │Sentiment │                        │   │
│  │  │  Agent  │ │  Workflow  │ │  ML Agent│                        │   │
│  │  └─────────┘ └────────────┘ └──────────┘                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │  Decision Support   │  │  Data Provider Layer                     │  │
│  │  build_decision_aids│  │  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  – score            │  │  │  yFinance    │  │  Polygon.io API  │  │  │
│  │  – checklist        │  │  │  Provider    │  │  (optional)      │  │  │
│  │  – instrument_plays │  │  └──────┬───────┘  └────────┬─────────┘  │  │
│  │  – volatility       │  │         └──────────┬─────────┘            │  │
│  │  – position_sizing  │  │              ┌──────┴──────┐               │  │
│  │  – options_metrics  │  │              │ Redis Cache │               │  │
│  └─────────────────────┘  │              │ (optional)  │               │  │
│                            │              └─────────────┘               │  │
│                            └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                    │                           │
          ┌─────────┘                           └──────────┐
          ▼                                               ▼
┌──────────────────┐                         ┌────────────────────────┐
│   PostgreSQL 16  │                         │   Observability Stack  │
│                  │                         │                        │
│  api_key         │                         │  Prometheus /metrics   │
│  watchlist       │                         │  OpenTelemetry traces  │
│  watchlist_symbol│                         │  Structlog JSON logs   │
│  alert           │                         │  Correlation-Id header │
│  batch_job       │                         └────────────────────────┘
│  analysis_run    │
│  agent_artifact  │
└──────────────────┘
```

---

## System Design Workflow

```
                              USER REQUEST
                                   │
                    ┌──────────────▼──────────────┐
                    │   Rate Limiter (slowapi)     │
                    │   30/min analysis            │
                    │   200/min default            │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   Auth Middleware            │
                    │   X-API-Key → bcrypt hash   │
                    │   lookup in api_key table   │
                    └──────────────┬──────────────┘
                                   │
               ┌───────────────────▼───────────────────┐
               │          Supervisor.stream_analysis()  │
               │                                        │
               │  1. Open AnalysisRun record (DB)       │
               │  2. Build AgentContext + Provider      │
               └───────────────────┬───────────────────┘
                                   │
          ┌────────────────────────▼────────────────────────┐
          │         asyncio.create_task × 7                  │
          │                                                  │
          │  ┌──────────┐                                    │
          │  │Market    │──► quote, price, change, vol       │
          │  │DataAgent │                                    │
          │  └──────────┘                                    │
          │  ┌──────────────┐                                │
          │  │Fundamentals  │──► P/E, market cap, sector     │
          │  │Agent         │                                │
          │  └──────────────┘                                │
          │  ┌──────────────┐                                │
          │  │Technicals    │──► SMA/EMA/RSI/MACD/ATR/OBV   │
          │  │Agent         │    trend_hint, 52-wk range     │
          │  └──────────────┘                                │
          │  ┌──────────────┐                                │
          │  │Financials    │──► annual price history bars   │
          │  │Agent         │                                │
          │  └──────────────┘                                │
          │  ┌──────────────┐                                │
          │  │Options       │──► ATM IV, implied move,       │
          │  │Agent         │    chain liquidity, expiry     │
          │  └──────────────┘                                │
          │  ┌──────────────┐                                │
          │  │RiskPro       │──► earnings window, checklist  │
          │  │WorkflowAgent │    earnings_days_away          │
          │  └──────────────┘                                │
          │  ┌──────────────┐                                │
          │  │SentimentML   │──► ML forecast signal,         │
          │  │Agent         │    sentiment_score, headlines  │
          │  └──────────────┘                                │
          │                                                  │
          │  asyncio.wait(FIRST_COMPLETED) ──► SSE event    │
          │  emitted per agent as it finishes               │
          └────────────────────────┬────────────────────────┘
                                   │ all 7 done
                    ┌──────────────▼──────────────┐
                    │  build_decision_aids()       │
                    │  • stock_vs_options_score    │
                    │  • checklist (8 items)       │
                    │  • instrument_plays (4)      │
                    │  • volatility context        │
                    │  • position sizing hints     │
                    │  • options_metrics_table     │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Supervisor._merge()         │
                    │                              │
                    │  market data OK?             │
                    │  ├─ No  → insufficient_data  │
                    │  earnings imminent?          │
                    │  ├─ Yes + mixed → options   │
                    │  IV elevated (>35%)?         │
                    │  ├─ Yes → options (credit)  │
                    │  directional clarity?        │
                    │  ├─ Yes + low IV → stock    │
                    │  └─ balanced → score-driven │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Persist to PostgreSQL       │
                    │  • AnalysisRun (verdict_json)│
                    │  • AgentArtifact × 7        │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  SSE: {"type":"verdict",...} │
                    │  SSE: {"type":"done"}        │
                    │  → Client renders full UI   │
                    └─────────────────────────────┘
```

---

## Agent Pipeline

```
                    ┌─────────────────────────────┐
                    │       AgentContext           │
                    │  symbol, timeout_s, provider │
                    └──────────────┬──────────────┘
                                   │
          ┌──────────┬─────────────┼────────────┬──────────┬──────────┐
          ▼          ▼             ▼            ▼          ▼          ▼
    ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐
    │ Market   │ │Fundmtl │ │Technical │ │Financial │ │Optns │ │Sentiment │
    │ Data     │ │        │ │          │ │          │ │      │ │   ML     │
    ├──────────┤ ├────────┤ ├──────────┤ ├──────────┤ ├──────┤ ├──────────┤
    │get_quote │ │get_fund │ │get_price │ │get_price │ │get_  │ │FinBERT / │
    │          │ │amentals │ │_history  │ │_history  │ │optns │ │StockPred │
    │last_price│ │pe_ratio │ │SMA20/50  │ │bar_count │ │ATM_IV│ │API call  │
    │day_chg%  │ │mkt_cap  │ │EMA20/200 │ │summary   │ │chain │ │          │
    │volume    │ │sector   │ │RSI7/14   │ │          │ │liq   │ │forecast_ │
    │          │ │rev_grwth│ │MACD6/13  │ │          │ │impl_ │ │signal    │
    │          │ │fwd_pe   │ │ATR14/50  │ │          │ │move  │ │sentiment_│
    │          │ │         │ │OBV       │ │          │ │      │ │score     │
    │          │ │         │ │52wk hi/lo│ │          │ │      │ │          │
    │          │ │         │ │trend_hint│ │          │ │      │ │          │
    └─────┬────┘ └────┬────┘ └─────┬────┘ └─────┬────┘ └──┬───┘ └────┬─────┘
          │           │            │             │          │          │
          └───────────┴────────────┴──────┬──────┴──────────┴──────────┘
                                          │
                                 ┌────────▼────────┐
                                 │   RiskPro       │
                                 │ WorkflowAgent   │
                                 │                 │
                                 │ earningsDate    │
                                 │ earnings_days   │
                                 │ has_upcoming_   │
                                 │ checklist[2]    │
                                 └────────┬────────┘
                                          │
                                 ┌────────▼────────┐
                                 │   Supervisor    │
                                 │   _merge()      │
                                 └─────────────────┘

  Each agent result shape:
  ┌────────────────────────────────────────────────┐
  │  agent_name   : str                            │
  │  status       : complete | degraded | failed   │
  │  error_message: str | None                     │
  │  provenance   : { source, fetched_at, latency }│
  │  <agent fields>: e.g. last_price, rsi_14, ...  │
  └────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌──────────────────────┐         ┌─────────────────────────┐
│       api_key        │         │        watchlist         │
├──────────────────────┤         ├─────────────────────────┤
│ id          UUID  PK │◄────────│ api_key_id   UUID  FK   │
│ name        TEXT     │    1:N  │ id           UUID  PK   │
│ key_prefix  VARCHAR  │         │ name         VARCHAR     │
│ key_hash    VARCHAR  │         │ description  TEXT        │
│ is_active   BOOLEAN  │         │ created_at   TIMESTAMPTZ │
│ created_at  TSTZ     │         └────────────┬────────────┘
│ last_used_at TSTZ    │                      │ 1:N
└──────────────────────┘         ┌────────────▼────────────┐
         │ 1:N                   │     watchlist_symbol     │
         │                       ├─────────────────────────┤
┌────────▼─────────────┐         │ id           UUID  PK   │
│        alert         │         │ watchlist_id UUID  FK   │
├──────────────────────┤         │ symbol       VARCHAR     │
│ id          UUID  PK │         │ note         TEXT        │
│ api_key_id  UUID  FK │         │ added_at     TIMESTAMPTZ │
│ symbol      VARCHAR  │         │ UNIQUE(watchlist_id,     │
│ condition   VARCHAR  │         │        symbol)           │
│ threshold_value FLOAT│         └─────────────────────────┘
│ threshold_verdict STR│
│ is_active   BOOLEAN  │
│ triggered_at TSTZ    │
│ created_at  TSTZ     │         ┌─────────────────────────┐
└──────────────────────┘         │       batch_job          │
                                 ├─────────────────────────┤
                                 │ id             UUID  PK  │
                                 │ status         VARCHAR   │
                                 │ universe       VARCHAR   │
                                 │ total_symbols  INTEGER   │
                                 │ completed_syms INTEGER   │
                                 │ failed_symbols INTEGER   │
                                 │ batch_key      VARCHAR   │
                                 │ symbols_json   JSONB     │
                                 │ composition_as_of DATE   │
                                 │ requested_at   TSTZ      │
                                 │ started_at     TSTZ      │
                                 │ finished_at    TSTZ      │
                                 └────────────┬────────────┘
                                              │ 1:N
                                 ┌────────────▼────────────┐
                                 │      analysis_run        │
                                 ├─────────────────────────┤
                                 │ id                UUID PK│
                                 │ symbol            VARCHAR│
                                 │ status            VARCHAR│
                                 │ started_at        TSTZ   │
                                 │ finished_at       TSTZ   │
                                 │ instrument_rec    VARCHAR│
                                 │ confidence_note   TEXT   │
                                 │ verdict_json      JSONB  │
                                 │ last_price        FLOAT  │
                                 │ portfolio_value   FLOAT  │
                                 │ max_risk_pct      FLOAT  │
                                 │ batch_job_id      UUID FK│
                                 │ IDX(symbol, started_at) │
                                 └────────────┬────────────┘
                                              │ 1:N
                                 ┌────────────▼────────────┐
                                 │      agent_artifact      │
                                 ├─────────────────────────┤
                                 │ id          UUID  PK     │
                                 │ run_id      UUID  FK     │
                                 │ agent_name  VARCHAR      │
                                 │ status      VARCHAR      │
                                 │ latency_ms  FLOAT        │
                                 │ error_message TEXT       │
                                 │ payload_json  JSONB      │
                                 │ recorded_at   TSTZ       │
                                 └─────────────────────────┘
```

---

## Frontend Pages

| Route | Description |
|---|---|
| `/` | **Analysis** — symbol input, SSE-streamed agent grid, verdict card, technicals, trade guidance, price forecast, options panels, decision aids, history |
| `/market-grid` | **Market Grid** — live auto-refreshing table of 40 symbols with 14 columns; add/remove symbols; configurable refresh interval |
| `/watchlists` | **Watchlists** — create named lists, add/remove symbols, click-through to analysis |
| `/alerts` | **Alerts** — set price-above / price-below / verdict-changes-to triggers per symbol |
| `/keys` | **API Keys** — create, list, and revoke API keys |

### Key Frontend Components

```
src/
├── app/
│   ├── page.tsx                  ← Analysis home (SSE streaming)
│   ├── market-grid/page.tsx      ← Live market grid
│   ├── watchlists/page.tsx
│   ├── alerts/page.tsx
│   └── keys/page.tsx
├── components/
│   ├── analysis/
│   │   ├── AgentStatusGrid.tsx   ← 7-card live agent status (pending → done)
│   │   ├── AgentStatusCard.tsx   ← Individual agent card with pulsing state
│   │   ├── VerdictCard.tsx       ← Main recommendation badge
│   │   ├── PriceForecastPanel.tsx← Rules-based 1d/5d/10d price forecast
│   │   ├── TradeGuidancePanel.tsx← Entry/stop/target guidance
│   │   ├── TechnicalIndicatorsPanel.tsx
│   │   ├── DecisionAidsPanel.tsx ← Full decision-support breakdown
│   │   ├── OptionsAnalysisPanel.tsx
│   │   ├── OptionsMetricsTable.tsx
│   │   ├── OptionsGuidanceCard.tsx
│   │   ├── AnalysisHistory.tsx   ← Past runs for the same symbol
│   │   ├── AnalysisLoader.tsx    ← Elapsed-time loader
│   │   └── LivePriceBar.tsx      ← Real-time quote strip
│   ├── market/
│   │   └── MarketGrid.tsx        ← 14-column scrollable table
│   ├── watchlists/
│   ├── alerts/
│   ├── keys/
│   ├── layout/
│   │   ├── NavBar.tsx
│   │   ├── Providers.tsx
│   │   └── DisclaimerBanner.tsx
│   └── ui/
│       ├── StatusDot.tsx
│       ├── Badge.tsx
│       ├── ScoreMeter.tsx
│       └── ErrorMessage.tsx
├── contexts/
│   ├── AnalysisContext.tsx       ← SSE state: partialContributions, verdict
│   └── ApiKeyContext.tsx
├── lib/
│   └── api.ts                   ← All fetch + streamAnalysis() helpers
└── types/
    └── api.ts                   ← TypeScript mirrors of Pydantic schemas
```

---

## API Reference

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/analysis/run` | Run analysis (blocking, returns full verdict) |
| `GET`  | `/v1/analysis/run/{symbol}` | Same as POST, GET convenience wrapper |
| `GET`  | `/v1/analysis/stream/{symbol}` | **SSE stream** — agent_done events + verdict |
| `GET`  | `/v1/analysis/history/{symbol}?limit=20` | Past completed runs for a symbol |

**SSE event types:**

```json
// One per agent as it completes:
{ "type": "agent_done", "agent": "MarketDataAgent", "status": "complete",
  "headline": "$213.12, +0.86%, Vol 43.7M", "detail": null }

// After all 7 agents finish:
{ "type": "verdict", "data": { ...full SupervisorVerdict... } }

// End of stream:
{ "type": "done" }
```

### Market Grid

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/market/quotes?symbols=AAPL,MSFT,...` | Batch live quotes, up to 50 symbols |

**Response fields per row:**
`symbol`, `pre_mkt_price`, `pre_mkt_change`, `last_price`, `change`, `post_mkt_price`, `post_mkt_change`, `earnings_date`, `market_cap`, `div_payment_date`, `exchange`, `week_52_high`, `week_52_low`, `shares_outstanding`

### Batch Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/analysis/batch` | Submit batch job (top10 / top100 / full / custom) |
| `GET`  | `/v1/analysis/batch/{job_id}` | Poll job status and counters |

### Watchlists

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`    | `/v1/watchlists` | List all watchlists for the API key |
| `POST`   | `/v1/watchlists` | Create a new watchlist |
| `DELETE` | `/v1/watchlists/{id}` | Delete a watchlist |
| `GET`    | `/v1/watchlists/{id}/symbols` | List symbols in a watchlist |
| `POST`   | `/v1/watchlists/{id}/symbols` | Add a symbol |
| `DELETE` | `/v1/watchlists/{id}/symbols/{symbol}` | Remove a symbol |

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`    | `/v1/alerts` | List all active alerts |
| `GET`    | `/v1/alerts/triggered` | List triggered alerts |
| `POST`   | `/v1/alerts` | Create alert (`price_above` / `price_below` / `verdict_changes_to`) |
| `DELETE` | `/v1/alerts/{id}` | Delete an alert |

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST`   | `/v1/auth/keys` | Create a new API key |
| `GET`    | `/v1/auth/keys` | List all API keys |
| `DELETE` | `/v1/auth/keys/{id}` | Revoke a key |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/healthz` | Health check |
| `GET`  | `/v1/quote/live/{symbol}` | Lightweight live quote |
| `POST` | `/v1/ingest/warm` | Pre-warm Redis cache for a symbol list |
| `GET`  | `/metrics` | Prometheus metrics endpoint |

---

## Technology Stack

### Backend

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI 0.109+ |
| ASGI server | Uvicorn (standard) |
| Data validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Database | PostgreSQL 16 (asyncpg driver) |
| Cache | Redis 7 (optional) |
| Market data | yfinance (default), Polygon.io (optional) |
| ML sentiment | FinBERT via HuggingFace Transformers / external StockPrediction API |
| Rate limiting | SlowAPI (redis-backed in prod) |
| Observability | structlog · OpenTelemetry · Prometheus |
| Testing | pytest + pytest-asyncio · 217 tests · ≥ 80% coverage |
| Linting | Ruff |

### Frontend

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | React Context (AnalysisContext, ApiKeyContext) |
| Streaming | fetch + ReadableStream SSE parser |
| HTTP client | Native fetch |
| Storage | localStorage (symbol lists, refresh interval) |

### Infrastructure

| Component | Technology |
|-----------|-----------|
| Containers | Docker Compose (Postgres + Redis) |
| CI-ready | Dockerfile included |
| Tracing | OpenTelemetry → OTLP gRPC exporter |
| Metrics | Prometheus `/metrics` |
| Logging | structlog JSON → stdout |

---

## Configuration

All settings can be overridden via environment variables or a `.env` file in the project root.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://rec:rec@localhost:5433/recommendation` | Postgres connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `USE_REDIS` | `false` | Enable Redis quote cache |
| `POLYGON_API_KEY` | *(none)* | Enable Polygon.io provider (falls back to yfinance) |
| `STOCK_PREDICTION_API_URL` | *(none)* | External ML API for SentimentMLAgent |
| `AGENT_TIMEOUT_SECONDS` | `45.0` | Per-agent hard timeout |
| `QUOTE_STALE_SECONDS` | `120` | Cache TTL |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins (`*` = dev wildcard) |
| `RATE_LIMIT_ANALYSIS` | `30/minute` | Rate limit for `/v1/analysis/*` |
| `RATE_LIMIT_BATCH` | `5/minute` | Rate limit for batch jobs |
| `RATE_LIMIT_DEFAULT` | `200/minute` | Global fallback |
| `METRICS_ENABLED` | `true` | Expose Prometheus `/metrics` |
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry tracing |
| `OTEL_ENDPOINT` | *(empty)* | OTLP gRPC endpoint (empty → console exporter) |
| `LOG_LEVEL` | `INFO` | structlog log level |
| `BATCH_CONCURRENCY` | `5` | Concurrent symbols per batch job |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for Postgres + Redis)

### 1. Start infrastructure

```powershell
cd D:\Study\AILearning\MLProjects\StockRecommendationPlatform
docker compose up -d
```

### 2. Install Python dependencies

```powershell
# Uses shared venv at D:\Study\AILearning\shared_Environment
pip install -r requirements.txt
```

### 3. Run database migrations

```powershell
alembic upgrade head
```

### 4. Start the backend

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

- API docs: http://127.0.0.1:8010/docs
- Health: http://127.0.0.1:8010/healthz

### 5. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

- App: http://localhost:3000
- Market Grid: http://localhost:3000/market-grid

### 6. Create an API key

```bash
curl -X POST http://localhost:8010/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "my-key"}'
```

Copy the returned `key` value into the API Keys page in the browser or set `X-API-Key` header on requests.

### 7. Run your first analysis

```bash
# Blocking
curl "http://localhost:8010/v1/analysis/run/AAPL?portfolio_value_usd=100000&max_risk_per_trade_pct=1"

# SSE stream (watch agents appear one by one)
curl -N "http://localhost:8010/v1/analysis/stream/NVDA"
```

---

## Running Tests

```powershell
# All tests
pytest -q

# With coverage report
pytest -q --cov=app --cov-report=term-missing

# Single file
pytest tests/test_agents.py -v
```

**Test suite:** 217 tests across 15 test files covering agents, supervisor, providers (yfinance, Polygon, Redis cache), watchlists router, alerts trigger, batch jobs, API hardening, observability, and options metrics.

---

## Docker Setup

```yaml
# docker-compose.yml provisions:
#   postgres:5433  (rec/rec/recommendation)
#   redis:6379
docker compose up -d
docker compose logs -f
docker compose down -v   # destroy volumes
```

To run the full stack in containers, build the app image:

```powershell
docker build -t stockresearch-api .
docker run -p 8010:8010 \
  -e DATABASE_URL=postgresql+asyncpg://rec:rec@postgres:5432/recommendation \
  -e REDIS_URL=redis://redis:6379/0 \
  -e USE_REDIS=true \
  stockresearch-api
```

---

## Project Structure

```
StockRecommendationPlatform/
├── app/
│   ├── agents/
│   │   ├── base.py              ← AgentBase, AgentContext, safe_run()
│   │   ├── market_data.py       ← MarketDataAgent
│   │   ├── fundamentals.py      ← FundamentalsAgent
│   │   ├── technicals.py        ← TechnicalsAgent (SMA/EMA/RSI/MACD/ATR)
│   │   ├── financials.py        ← FinancialsAgent
│   │   ├── options.py           ← OptionsAgent (ATM IV, chain, implied move)
│   │   ├── risk_pro.py          ← RiskProWorkflowAgent (earnings calendar)
│   │   └── sentiment_ml.py      ← SentimentMLAgent (FinBERT / external API)
│   ├── providers/
│   │   ├── base.py              ← MarketDataProvider ABC
│   │   ├── yfinance_provider.py ← Default async yfinance wrapper
│   │   ├── polygon_provider.py  ← Polygon.io REST client
│   │   ├── redis_cache.py       ← Redis caching decorator
│   │   └── factory.py           ← build_provider() — selects & wraps provider
│   ├── routers/
│   │   ├── auth.py              ← API key CRUD
│   │   ├── watchlists.py        ← Watchlist + symbol management
│   │   └── alerts.py            ← Alert CRUD + _evaluate_alert()
│   ├── db/
│   │   ├── models.py            ← SQLAlchemy ORM models
│   │   └── session.py           ← Async engine + get_session()
│   ├── schemas/
│   │   ├── agents.py            ← Pydantic output schemas + SupervisorVerdict
│   │   ├── user.py              ← Watchlist / Alert request/response schemas
│   │   └── batch.py             ← BatchJob schemas
│   ├── supervisor.py            ← Supervisor: run_analysis() + stream_analysis()
│   ├── decision_support.py      ← build_decision_aids() — score, checklist, plays
│   ├── batch.py                 ← Background batch runner
│   ├── ingest.py                ← warm_cache() for Redis pre-warming
│   ├── auth.py                  ← get_current_key() dependency
│   ├── config.py                ← Settings (pydantic-settings)
│   ├── limiter.py               ← SlowAPI rate limiter instance
│   ├── middleware.py            ← CorrelationId + SecurityHeaders middleware
│   ├── observability.py         ← structlog + OTEL + Prometheus setup
│   ├── universe.py              ← TOP_10, TOP_100, get_sp500()
│   └── main.py                  ← FastAPI app, all routes
├── alembic/
│   └── versions/
│       ├── 0001_initial_schema.py
│       ├── 0002_batch_job.py
│       └── 0003_watchlists_alerts.py
├── frontend/
│   └── src/  (Next.js 14 app)
├── tests/
│   ├── test_agents.py
│   ├── test_alerts_trigger.py
│   ├── test_api_hardening.py
│   ├── test_auth_watchlists_alerts.py
│   ├── test_batch.py
│   ├── test_batch_run.py
│   ├── test_ingest.py
│   ├── test_main_endpoints.py
│   ├── test_observability.py
│   ├── test_options_metrics.py
│   ├── test_providers.py
│   ├── test_providers_impl.py
│   ├── test_supervisor_and_decision.py
│   ├── test_supervisor_integration.py
│   ├── test_supervisor_resilience.py
│   └── test_watchlists_router.py
├── docs/
│   └── MASTER_PLAN.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── pytest.ini
```

---

## Decision Support Output Example

```json
{
  "instrument_recommendation": "options",
  "confidence_note": "IV looks elevated vs simple heuristics — options structures may be efficient.",
  "options": {
    "strategy_family": "premium_selling_or_covered_call",
    "rationale_codes": ["iv_elevated", "no_imminent_earnings_flag"],
    "strike_guidance": "OTM calls for covered calls or OTM credit spreads vs support/resistance.",
    "max_loss_scenario": "For credit spreads: width minus credit."
  },
  "decision_aids": {
    "stock_vs_options_score": -0.42,
    "checklist": [...],
    "volatility": {
      "regime": "elevated",
      "atm_iv": 0.38,
      "implied_move_1d_pct": 2.4
    },
    "position_sizing": [...]
  },
  "technicals": {
    "sma_20": 213.5, "sma_50": 195.2,
    "rsi_14": 68.2, "atr_pct_14": 2.1,
    "trend_hint": "bullish"
  }
}
```

---

> **Disclaimer:** This platform is a research and learning tool. All analysis outputs are hypothetical and for educational purposes only. Nothing here constitutes financial advice. Always consult a licensed financial professional before making investment decisions.
