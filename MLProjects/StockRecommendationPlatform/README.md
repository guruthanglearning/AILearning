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
7. [UI Guide — How Each Page Works](#ui-guide--how-each-page-works)
8. [API Reference](#api-reference)
9. [Technology Stack](#technology-stack)
10. [Configuration](#configuration)
11. [Quick Start](#quick-start)
12. [Running Tests](#running-tests)
13. [Docker Setup](#docker-setup)
14. [Project Structure](#project-structure)

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

The Analysis page also opens a **WebSocket** connection (`/v1/ws/quote/{symbol}`) for per-second live price updates. The backend relays Polygon.io's `wss://delayed.polygon.io/stocks` aggregates (Starter plan) to the browser — the `LivePriceBar` component shows a pulsing green **LIVE** indicator when connected and falls back to HTTP REST price when the WebSocket is unavailable.

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
                    │  Claude LLM Decision Engine  │
                    │  (claude-opus-4-8 default)   │
                    │                              │
                    │  All 7 agent outputs fed as  │
                    │  structured prompt context   │
                    │                              │
                    │  Returns:                    │
                    │  • instrument_recommendation │
                    │  • confidence_note           │
                    │  • options_guidance          │
                    │  • summary_headline          │
                    │  • user_answers (4 Q&A)      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  _validate_strike_guidance() │
                    │                              │
                    │  Cross-checks Claude's       │
                    │  options strikes against     │
                    │  real chain data; stamps     │
                    │  chain_validated + verified  │
                    │  leg strikes when quality=   │
                    │  "full"                      │
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
| `/market-grid` | **Market Grid** — live auto-refreshing table of 40 symbols with 14 columns; prices sourced from Polygon batch snapshot, supplementary fields from yfinance |
| `/momentum` | **Momentum** — cross-sectional momentum scores per GICS sector; sortable by 1M/3M/6M return, RSI, vs SPY; configurable top-N per sector |
| `/watchlists` | **Watchlists** — create named lists, add/remove symbols, click-through to analysis |
| `/alerts` | **Alerts** — set price-above / price-below / verdict-changes-to triggers per symbol |
| `/keys` | **API Keys** — create, list, and revoke API keys |
| `/logs` | **Logs** — real-time error log viewer showing per-agent failures with symbol, agent name, status, and stack detail |

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

## UI Guide — How Each Page Works

### 1. Analysis Page (`/`)

The main page is where you research a single stock and get a full AI-driven recommendation.

#### How to run an analysis

1. Type a US ticker symbol in the search box (e.g. `NVDA`, `AAPL`, `TSLA`).
2. Optionally set **Portfolio Value ($)** and **Max Risk % per trade** — these are used to size positions.
3. Click **Analyse** (or press Enter). The 7 agent cards immediately start lighting up as each agent finishes (SSE streaming — no page reload).

#### Agent Status Grid (7 cards)

Each card represents one specialist agent running in parallel. Cards transition through three states:

| State | Visual | Meaning |
|-------|--------|---------|
| **Pending** | Grey pulsing dot | Agent has not yet returned |
| **Complete** | Green dot + headline | Agent succeeded; headline shows key output |
| **Degraded / Failed** | Amber / Red dot | Agent timed out or errored; downstream still runs |

| Agent | What it returns |
|-------|----------------|
| **MarketDataAgent** | Last price, day change %, volume |
| **FundamentalsAgent** | Company name, sector, market cap, P/E, forward P/E, revenue growth |
| **TechnicalsAgent** | Trend hint, RSI-14, SMA20/50, EMA20, ATR — all computed from 252 daily bars |
| **FinancialsAgent** | Confirms price history bar count; flags if data is thin |
| **OptionsAgent** | ATM implied volatility, implied 1-day move %, nearest expiry, chain liquidity |
| **RiskProWorkflowAgent** | Earnings date, days-to-earnings, binary event risk flag |
| **SentimentMLAgent** | ML sentiment forecast (Bullish / Bearish), score, top headlines |

#### Live Price Bar

Sits at the top of the page. Shows a pulsing **LIVE** indicator (green) when the Polygon WebSocket is connected and streaming per-second price ticks. Falls back to REST poll when the market is closed or Polygon is unavailable.

#### Verdict Card

The main recommendation badge appears after all 7 agents complete:

| Badge | Meaning |
|-------|---------|
| **Long Stock** | Buy and hold the underlying — cleaner risk profile than options in this regime |
| **Options** | Options structures offer a better risk/reward — see the Options panel for the specific strategy |
| **No Trade** | Signals conflict or risk too high — pass for now |
| **Insufficient Data** | Too few data points to make a reliable recommendation |

Below the badge:
- **Confidence note** — Claude's plain-English reasoning (1–2 sentences)
- **Summary headline** — one-line trading thesis

#### Stock-vs-Options Score Meter

A number from **–1.0 to +1.0**:
- `+1.0` → strongly favours long stock
- `–1.0` → strongly favours options
- Near `0` → borderline; read the checklist for tie-breakers

#### Decision Checklist (5 items)

Each row is a pass/warn indicator:

| Item | Pass means | Warn means |
|------|-----------|------------|
| **Directional clarity** | Technicals lean clearly bullish or bearish | Mixed signals — size down or use defined-risk options |
| **Earnings window** | No earnings in the next ~2 weeks | Earnings imminent — avoid undefined-risk positions |
| **Options liquidity** | Chain is readable and spread is acceptable | Thin chain — wider bid/ask, harder to execute |
| **ML vs technicals** | ML signal agrees with technical trend | Divergence — treat ML as a secondary input only |
| **Volatility regime** | IV is cheap (long structures less penalised) or rich (premium-selling favoured) | IV regime unclear |

#### Technical Indicators Panel

Key values to read:

| Indicator | How to read it |
|-----------|---------------|
| **SMA20 / SMA50** | Price above both → uptrend. Price below SMA50 → bearish structure |
| **EMA20** | Short-term momentum. Crossing above SMA20 → momentum building |
| **RSI-14** | Below 30 = oversold, above 70 = overbought, 40–60 = neutral |
| **MACD histogram** | Positive and rising = bullish momentum, negative = weakening |
| **ATR-14 %** | Daily range as % of price — use as stop-distance guide (e.g. 1–2× ATR) |
| **OBV slope** | Positive = accumulation (buyers in control), negative = distribution |
| **52-wk High / Low** | Price near the high = momentum; near the low = mean-reversion candidate |
| **Trend hint** | `bullish` / `bearish` / `mixed` — derived from SMA stack and RSI |

#### Volatility Panel

| Field | How to read it |
|-------|---------------|
| **IV Regime** | `iv_cheap` = options cheaper than recent realized vol (good for long vol); `iv_rich` = premium-selling favoured |
| **ATM IV** | Annualised implied vol of the at-the-money option |
| **HV-20d** | Realized vol over last 20 days — compare to IV to gauge richness |
| **IV Rank 52w** | 0–100 percentile vs past year. Above 50 = IV rich; below 30 = IV cheap |
| **Implied move 1d %** | What the options market prices as the expected 1-day move |

#### Options Metrics Table

Only appears when options are relevant. Shows two pre-computed strategies with real chain strikes:

| Column | Meaning |
|--------|---------|
| **Strategy** | Bull Call Spread (debit) or Short Put Spread (credit) |
| **Legs** | Exact strikes and rights from the live chain |
| **Net Debit / Credit** | What you pay (debit) or receive (credit) per share × 100 |
| **Max Profit / Max Loss** | Best and worst case per contract |
| **Breakeven** | Price at expiry where you break even |
| **DTE** | Days to expiration |
| **Trend alignment** | Whether the structure direction matches the technical trend |
| **30% / 60% rule** | Standard exit targets — close at 30% of max profit (early/quick) or 60% (standard) |
| **Management rules** | When to close, defend, or roll |

#### Options Guidance Card

When Claude recommends options, this card shows:
- **Chain Verified** badge (green) — strikes were cross-checked against the real options chain
- **Verified strikes** — exact legs (e.g. `Buy $300 call / Sell $302.5 call exp 2026-06-22`)
- **Estimated** badge (amber) — Claude's guidance couldn't be verified against live chain data

#### 4 Pre-answered Questions (Q&A Panel)

Claude answers four standard risk-management questions for the specific symbol:
1. Is this speculative or a multi-month thesis?
2. What price level, time, or event invalidates the trade?
3. What is max loss in dollars?
4. Is option assignment acceptable?

Read these before entering any position — they encode the stop-loss logic and trade sizing context.

#### Analysis History

Below the main result, past analyses for the same symbol are listed (most recent first) with the verdict and price at the time. Useful for tracking how the recommendation changed over time.

---

### 2. Market Grid (`/market-grid`)

A live scrollable table of up to 40 symbols with 14 columns, sorted by market cap (largest first) by default.

#### Controls

| Control | What it does |
|---------|-------------|
| **Add Symbol** | Type a ticker and press Enter or click Add — appends to the grid and persists in localStorage |
| **× chip** | Remove a symbol from the grid |
| **Refresh (sec)** | Set auto-refresh interval (5–300s). Default 10s. Price data is re-fetched on each cycle |
| **↻ Refresh now** | Immediately re-fetch all prices |
| **Live / Offline dot** | Green pulsing = Polygon WebSocket connected and streaming per-second ticks. Grey = disconnected (after hours or no Polygon key) |
| **Sort headers** | Click any column header to sort. Numeric columns default to descending (highest first) |

#### Column Reference

| Column | What it shows | How to read it |
|--------|--------------|---------------|
| **Symbol** | Ticker — click to run full analysis | Blue = clickable |
| **Pre-Mkt Price** | Price from the pre-market session | Only populated during pre-market hours (4–9:30 AM ET) |
| **Pre-Mkt Change** | % change during pre-market | Green = up, red = down |
| **Last Price** | Most recent price | Flashes **green** (price ticked up) or **red** (price ticked down) during market hours via WebSocket. Small pulsing dot = live feed active for this row |
| **Change** | Day change % from prior close | Green = up, red = down |
| **Post-Mkt Price** | Price from after-hours session | Only populated during after-hours (4–8 PM ET) |
| **Post-Mkt Change** | % change after hours | |
| **Earnings Date** | Next reported earnings date | Use to avoid holding through an earnings event |
| **Market Cap** | Total market capitalisation | T = trillion, B = billion, M = million |
| **Div Payment Date** | Next dividend payment date | Relevant for covered call / cash-secured put holders |
| **Exchange** | Listing exchange (NMS = Nasdaq, NYQ = NYSE) | |
| **52-Wk High** | Highest price in the last 52 weeks | Price near high = momentum; far below = potential value or breakdown |
| **52-Wk Low** | Lowest price in the last 52 weeks | |
| **Shares Out** | Shares outstanding | Large float = easier to trade; used with volume to gauge liquidity |

#### Live Price Updates

During market hours (9:30 AM – 4:00 PM ET):
- Each Last Price cell **flashes green** when a price tick arrives above the previous price, or **red** if below.
- The flash lasts 900ms then fades back to white.
- A small pulsing **emerald dot** appears next to the price while that symbol is receiving live ticks.
- Data is sourced from Polygon.io (15-minute delayed on the Starter plan).

After market hours the WebSocket remains connected but no ticks flow — prices show the last known close.

---

### 3. Momentum Page (`/momentum`)

Shows cross-sectional momentum scores for top stocks grouped by GICS sector.

#### How to use it

- Use the **Top N per sector** control to limit results (default 5).
- Sort by **1M**, **3M**, or **6M return**, **RSI**, or **vs SPY** to find leaders vs laggards.
- Stocks with high scores across multiple timeframes are momentum leaders — likely showing sustained institutional interest.
- **vs SPY** column shows relative outperformance — positive = beating the market.

#### How to read momentum scores

| Score range | Meaning |
|------------|---------|
| High positive momentum + RSI 50–70 | Healthy trend, not yet overbought — potential entry |
| High positive momentum + RSI > 70 | Extended — wait for a pullback or use options to sell premium |
| Negative momentum across timeframes | Avoid or consider short-side plays if directional |

---

### 4. Watchlists (`/watchlists`)

Organise symbols into named lists for faster tracking.

#### How to use it

1. Click **New Watchlist** → give it a name (e.g. "Tech Core", "Dividend Income").
2. Click into a watchlist → **Add Symbol** → type a ticker.
3. Click a symbol to jump directly to its analysis page.
4. Delete a symbol with the **×** button, or delete the entire list with **Delete watchlist**.

Watchlists are scoped to your **API key** — each key has its own set.

---

### 5. Alerts (`/alerts`)

Set automatic triggers on price levels or recommendation changes.

#### Alert types

| Type | Triggers when |
|------|--------------|
| **price_above** | Last price crosses above your threshold |
| **price_below** | Last price falls below your threshold |
| **verdict_changes_to** | Analysis recommendation changes to a specified value (e.g. `stock`, `options`, `no_trade`) |

#### How to create an alert

1. Click **New Alert**.
2. Enter a symbol, select condition type, and enter the threshold value.
3. Click **Save**. The alert is active immediately.

#### Reading triggered alerts

The **Triggered** tab shows alerts that have fired, with the timestamp. Triggered alerts are marked inactive — create a new one to re-arm.

---

### 6. API Keys (`/keys`)

Manage authentication keys for the platform API.

#### How to use it

1. Click **Create Key** → give it a name.
2. **Copy the key immediately** — it is only shown once in full.
3. Paste the key into the **API Key** field shown in the top-right of the UI, or set the `X-API-Key` HTTP header when calling the API directly.
4. Revoke a key with **Delete** — all watchlists and alerts associated with it are removed.

The key prefix (first 8 chars) is shown in the list so you can identify which key is which.

---

### 7. Logs Page (`/logs`)

Real-time error log viewer for diagnosing agent failures.

#### How to read it

Each row shows:

| Column | Meaning |
|--------|---------|
| **Time** | When the error occurred (local time) |
| **Symbol** | The ticker that was being analysed |
| **Agent** | Which of the 7 agents failed |
| **Status** | `degraded` (partial data returned) or `failed` (no data) |
| **Error** | The exception message or timeout reason |

#### Common errors and what they mean

| Error message | Likely cause |
|--------------|-------------|
| `timeout` | Agent exceeded the `AGENT_TIMEOUT_SECONDS` limit (default 45s) — data provider was slow |
| `network error` | yfinance or Polygon couldn't reach the data source |
| `insufficient_data` | Less than 60 price bars returned — technicals will be degraded |
| `chain empty` | Options chain returned no strikes — OptionsAgent degraded |

A degraded agent does **not** stop the analysis — the Supervisor proceeds with whatever data is available and Claude works with what it has.

---

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

### Momentum

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/momentum/sectors?top_n=5` | Top-N momentum stocks per GICS sector (cross-sectional scoring) |

### WebSocket

| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/v1/ws/quote/{symbol}` | Real-time per-second price updates via Polygon WebSocket relay (`wss://delayed.polygon.io/stocks`). Requires `POLYGON_API_KEY`. Falls back to HTTP REST when unavailable. |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/healthz` | Health check |
| `GET`  | `/v1/quote/live/{symbol}` | Lightweight live quote |
| `POST` | `/v1/ingest/warm` | Pre-warm Redis cache for a symbol list |
| `GET`  | `/metrics` | Prometheus metrics endpoint |
| `GET`  | `/v1/claude/models` | List available Claude models with pricing |
| `GET`  | `/v1/claude/usage` | Session token usage and estimated cost per model |

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
| Market data | yfinance (default), Polygon.io REST + WebSocket (optional) |
| LLM decision engine | Anthropic Claude (Opus 4.8 default; Sonnet 4.6 / Haiku 4.5 selectable per-analysis from UI) |
| ML sentiment | FinBERT via HuggingFace Transformers / external StockPrediction API |
| Rate limiting | SlowAPI (redis-backed in prod) |
| Observability | structlog · OpenTelemetry · Prometheus |
| Testing | pytest + pytest-asyncio · 325 tests · ≥ 80% coverage |
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
| `ANTHROPIC_API_KEY` | *(required)* | Claude API key — needed for the LLM decision engine |

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

**Test suite:** 325 tests across 20 test files covering agents, supervisor, providers (yfinance, Polygon, Redis cache), watchlists router, alerts trigger, batch jobs, API hardening, observability, options metrics, Polygon WebSocket relay, decision support extras, and main cache/endpoints.

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
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_alerts_trigger.py
│   ├── test_api_hardening.py
│   ├── test_auth_watchlists_alerts.py
│   ├── test_batch.py
│   ├── test_batch_run.py
│   ├── test_decision_support_extras.py
│   ├── test_ingest.py
│   ├── test_main_cache_and_endpoints.py
│   ├── test_main_endpoints.py
│   ├── test_observability.py
│   ├── test_options_metrics.py
│   ├── test_polygon_ws.py
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
    "max_loss_scenario": "For credit spreads: width minus credit.",
    "chain_validated": true,
    "chain_verified_strikes": "Sell $215 put / Buy $210 put exp 2026-07-18",
    "validated_legs": [
      {"right": "put", "strike": 215.0, "quantity_signed": -1, "leg_type": "short"},
      {"right": "put", "strike": 210.0, "quantity_signed": 1,  "leg_type": "long"}
    ]
  },
  "decision_aids": {
    "stock_vs_options_score": -0.42,
    "checklist": [...],
    "volatility": {
      "regime": "iv_rich",
      "atm_iv": 0.38,
      "hv_20d_annualized": 0.28,
      "iv_rank_52w": 72,
      "implied_move_1d_pct": 2.4
    },
    "options_metrics_table": [
      {
        "template_id": "short_put_spread",
        "strategy_label": "Short Put Spread (Credit Vertical)",
        "expiration": "2026-07-18",
        "legs": [...],
        "net_debit_credit": 0.85,
        "max_profit": 0.85,
        "max_loss": 4.15,
        "row_data_quality": "full"
      }
    ],
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
