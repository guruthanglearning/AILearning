# Stock Recommendation Platform - Interview Explanation Guide

## 📋 Quick Project Summary

**Project**: Multi-Agent AI Stock Research Platform
**Core Output**: Stock vs. Options recommendation with full decision-support aids
**Architecture**: 7 specialist agents running in parallel + an LLM supervisor that synthesizes their output
**Tech Stack**: FastAPI, Next.js 14, PostgreSQL, Redis, Claude (multi-model) / GPT-4o mini, Docker, Kubernetes
**Scale**: 396 automated tests, 15 frontend pages, dual deployment (Docker Compose and Kubernetes) validated in parity

---

## 🎯 Opening Statement (30 seconds)

*"I built a stock research platform that runs 7 specialist AI agents in parallel — market data, fundamentals, technicals, financials, options, risk, and sentiment — then hands their structured output to an LLM supervisor (Claude, with GPT-4o mini available as an alternate, user-selectable provider) that synthesizes everything into a single stock-vs-options recommendation with a plain-English rationale. Results stream to the browser over SSE so each agent card lights up the moment it finishes, instead of waiting for the slowest one. It's deployed both as a Docker Compose stack and to Kubernetes, with Prometheus/Grafana monitoring and a 396-test suite backing it."*

---

## 🤖 The Architecture: 7 Agents + 1 Supervisor

### Why Multiple Agents Instead of One Big Model?

The core design decision was **separation of concerns**: each agent owns one narrow, well-defined data domain, computes deterministic quantitative signals, and reports a status (`complete | degraded | failed`) — never an opinion. Only the **Supervisor's LLM call** is asked to reason and recommend. This keeps the expensive, non-deterministic part of the system (the LLM) as small and well-scoped as possible, and keeps everything else fast, cheap, testable, and independently failure-isolated.

### The 7 Agents

| Agent | What It Computes | Data Source |
|---|---|---|
| **MarketDataAgent** | Last price, previous close, day change %, volume, market state (PRE/REGULAR/POST/CLOSED) | yfinance / Polygon.io |
| **FundamentalsAgent** | P/E ratio, forward P/E, market cap, sector, revenue growth | yfinance |
| **TechnicalsAgent** | SMA 20/50/200, EMA 20/200, RSI 7/14/200, MACD(6,13), ATR 14/50, OBV slope, 52-week range, trend hint | yfinance price history |
| **FinancialsAgent** | Annual price-history bar count + summary for financial statement context | yfinance |
| **OptionsAgent** | ATM implied volatility, nearest expiry, chain liquidity hint, implied 1-day move | yfinance / Polygon options chain |
| **RiskProWorkflowAgent** | Days to next earnings, upcoming-earnings flag, pre-trade risk checklist | yfinance earnings calendar |
| **SentimentMLAgent** | Sentiment score, forecast signal, top headlines | FinBERT (HuggingFace Transformers) over Finnhub news, or an external ML API |

All 7 run **concurrently** via `asyncio.gather` / `asyncio.wait(FIRST_COMPLETED)` inside a `Supervisor` class — a slow or failed agent doesn't block the others, and the SSE stream pushes each agent's card to the UI the instant it completes.

### The Supervisor + Claude Decision Engine

Once agent outputs are in, a **Decision Support** layer (`build_decision_aids`) pre-computes deterministic quantitative aids — a stock-vs-options score (-1 to +1), a pass/warn/fail checklist, volatility regime, position-sizing hints, and an options metrics table. Only *then* does the Supervisor hand all of this — structured, already-computed — to Claude via a `submit_analysis_verdict` tool call, so the LLM is reasoning over verified numbers instead of hallucinating them, and its structured-output contract is enforced by the tool schema rather than free-text parsing.

**Model selection is user-facing and cost-tracked**: the Analysis tab lets you pick Haiku 4.5 / Sonnet 4.6 / Opus 4.8 / Fable 5 / Fable 5.1 (Anthropic) or GPT-4o mini (OpenAI) per analysis, and a **Model Cost Comparison** card shows the actual billed cost for the model you picked alongside what every other model would have cost for the same token usage — including correctly attributing cost to whichever model *actually* served the response when Fable-tier's server-side refusal fallback kicks in, and correctly pricing Anthropic prompt-cache write/read tokens at their distinct rates.

---

## 🔄 Complete Workflow Example

### Real Analysis Request: `GET /v1/analysis/stream/AAPL`

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Rate limiter (slowapi, 30/min on analysis)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: 7 agents fan out concurrently (asyncio.gather)      │
├─────────────────────────────────────────────────────────────┤
│  MarketData   → $230.36, +0.45%, Vol 135.4M      (fastest)  │
│  Fundamentals → Cap $5.56T, sector Semiconductors            │
│  Technicals   → Trend: Bullish, RSI-14: 60.4                 │
│  Financials   → 252 annual bars available                    │
│  Options      → ATM IV 32.1%, ±3.87% implied move (slowest)  │
│  RiskPro      → No imminent earnings                         │
│  SentimentML  → Neutral (+0.018), FinBERT over recent news   │
│                                                                │
│  Each card streams to the browser via SSE as it finishes —  │
│  the UI never waits for the slowest agent to show progress. │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Decision Support (deterministic, no LLM)             │
├─────────────────────────────────────────────────────────────┤
│  stock_vs_options_score: +0.62 (leans stock)                 │
│  volatility regime: normal                                   │
│  checklist: PASS trend, PASS liquidity, WARN earnings-window │
│  options_metrics_table: strikes, greeks-adjacent guidance    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Claude tool call (submit_analysis_verdict)           │
├─────────────────────────────────────────────────────────────┤
│  Input: all 7 agent outputs + decision aids, formatted as    │
│         one structured prompt with a cached system prompt    │
│  Output (via tool schema, not free text):                    │
│    instrument_recommendation: "stock"                        │
│    confidence_note: "Bullish trend (RSI 60.4, SMA20>SMA50)   │
│      with normal IV — direct ownership is the capital-       │
│      efficient vehicle here."                                │
│    4 pre-trade Q&A pairs (thesis, invalidation, max loss,    │
│      assignment risk)                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Final: SupervisorVerdict streamed to browser                 │
├─────────────────────────────────────────────────────────────┤
│  Verdict card, decision aids panel, technicals, cost table   │
│  Persisted to Postgres (analysis_run + agent_artifact)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT  (Browser)                                │
│   Analysis (SSE live) · Market Grid · Momentum · Watchlists · Alerts   │
│                       Next.js 14  (TypeScript)                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │  HTTP / SSE / WebSocket
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FASTAPI  BACKEND  (Python 3.12)                     │
│  Middleware: SecurityHeaders → CorrelationId → SlowAPI → CORS           │
│  Supervisor: 7 agents (asyncio.gather) → Decision Support → Claude/GPT  │
│  Data Provider Layer: yfinance ⇄ Polygon.io ⇄ Redis cache               │
└────────────────────────────────┬────────────────────────────────────────┘
                    │                           │
          ┌─────────┘                           └──────────┐
          ▼                                               ▼
┌──────────────────┐                         ┌────────────────────────┐
│   PostgreSQL 16  │                         │   Observability Stack  │
│  api_key         │                         │  Prometheus /metrics   │
│  watchlist(_sym) │                         │  OpenTelemetry traces  │
│  alert           │                         │  Structlog JSON logs   │
│  batch_job       │                         │  Grafana dashboard     │
│  analysis_run    │                         └────────────────────────┘
│  agent_artifact  │
└──────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI + Uvicorn, Pydantic v2 |
| ORM / DB | SQLAlchemy 2.0 (async) + Alembic migrations → PostgreSQL 16 |
| Cache | Redis 7 (optional; TTL-cached market quotes) |
| Market data | yfinance (default), Polygon.io REST + WebSocket (optional, live price relay) |
| LLM decision engine | Anthropic Claude — Opus 4.8 (default), Sonnet 4.6, Haiku 4.5, Fable 5 / Fable 5.1 — or OpenAI GPT-4o mini, selectable per-analysis |
| ML sentiment | FinBERT (HuggingFace Transformers) over Finnhub news |
| Rate limiting | SlowAPI |
| Observability | structlog · OpenTelemetry · Prometheus · Grafana |
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS |
| Streaming | fetch + ReadableStream SSE parser (analysis), native WebSocket (live price) |
| Testing | pytest + pytest-asyncio, 396 tests, Ruff lint, GitHub Actions CI |
| Containers | Docker Compose (Postgres + Redis + backend + frontend + nginx + Prometheus + Grafana) |
| Orchestration | Kubernetes manifests — 2 backend + 2 frontend replicas, Postgres StatefulSet, Redis, NGINX Ingress, domain routing (`app.stockresearch.local`) |

---

## 🎯 Why This Architecture?

```
┌────────────────────────────────────────────────────────────┐
│ Design Goal → Technical Solution                            │
├────────────────────────────────────────────────────────────┤
│ ⚡ RESPONSIVENESS                                            │
│    → 7 agents run concurrently; SSE streams each card as    │
│      soon as it finishes instead of one big blocking wait   │
│                                                               │
│ 🎯 GROUNDED LLM OUTPUT (no hallucinated numbers)             │
│    → Deterministic agents + decision-support math compute   │
│      every number first; the LLM only reasons over them,    │
│      via a tool-call schema, not free-text parsing          │
│                                                               │
│ 💰 COST CONTROL & TRANSPARENCY                               │
│    → Per-analysis model selector + a live cost comparison   │
│      table across every available model, priced off actual  │
│      token usage (including prompt-cache tokens)             │
│                                                               │
│ 🔄 RESILIENCE                                                │
│    → Each agent reports complete/degraded/failed and the    │
│      Supervisor merges around failures instead of crashing; │
│      Claude Fable-tier requests opt into server-side         │
│      refusal fallback to Opus 4.8 automatically              │
│                                                               │
│ 📈 PARITY ACROSS ENVIRONMENTS                                │
│    → Identical feature set validated on both Docker Compose │
│      and Kubernetes via the same 19-check regression suite  │
└────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Challenges & Solutions

### Challenge 1: yfinance Rate-Limiting Took Two Separate Fixes
**Problem**: The Market Grid page polls `/v1/market/quotes` for ~40 symbols every 10 seconds by default. The first fix — an `asyncio.Semaphore(3)` bounding concurrent yfinance calls per request — stopped burst failures, but the bug **recurred within a day** because sustained polling volume alone (not burst size) was enough to retrip Yahoo's rate limiter with several browser tabs open.
**Solution**: A second, orthogonal layer — a per-symbol TTL cache (120s for successful fetches, a shorter 20s TTL for failed ones so it recovers quickly once the limit clears). **Takeaway used in interviews**: rate-limit mitigation for any bursty *and* sustained-poll workload needs both a concurrency bound and a cache — one alone isn't sufficient.

### Challenge 2: A Silent Feature Bug Found by Tracking Cost, Not by a Bug Report
**Problem**: While adding a new model (Fable 5) and validating its billing end-to-end, live cost tracking showed a Fable-selected analysis billed under Opus 4.8 instead. Root cause: the SSE streaming endpoint — the main Analysis page's primary flow — never accepted or forwarded a `claude_model` query parameter, so the model selector had **silently done nothing** on the main page since it was introduced.
**Solution**: Fixed both the streaming and blocking endpoints to accept and forward `claude_model`, confirmed via a regression test that specifically asserts the parameter reaches the LLM call. **Takeaway**: cost/usage instrumentation isn't just a monitoring nice-to-have — it caught a functional bug that no functional test alone would have surfaced, because the analysis still "worked," just with the wrong model silently substituted.

### Challenge 3: Infra That Caches Identity Needs an Explicit Refresh
**Problem**: After `docker compose up -d` recreated the backend container, nginx started returning 502s — nginx resolves and caches the upstream container's IP at first connection via Docker's embedded DNS, and a container recreate changes that IP.
**Solution**: `docker compose restart nginx` after recreating any service nginx proxies to. The same underlying class of bug also hit a Grafana datasource whose `uid` had drifted from what was already auto-provisioned — same fix pattern: anything that caches an identity needs an explicit refresh when the thing it points to changes.

### Challenge 4: Getting Accurate LLM Cost Comparisons Right Took Three Review Rounds
**Problem**: Building the per-model cost comparison table looked simple at first — apply each model's price to the token count — but an independent code review (OpenAI Codex CLI, run as part of the PR workflow) caught real accounting bugs: pricing a fallback-served response at the *requested* model's rate instead of the model that actually served it, ignoring Anthropic prompt-cache write/read tokens (billed at distinct 1.25x / 10% rates) entirely, and applying Anthropic-specific cache multipliers to a cross-provider (OpenAI) comparison row where they don't apply.
**Solution**: Fixed all three with targeted unit tests asserting the exact dollar math for each scenario (cache write, cache read, Fable-tier's cheaper 2.5% cache-read rate, and the fallback-attribution case). **Takeaway**: "compute a cost" sounds trivial but has real edge cases — a second independent reviewer caught what one careful pass missed.

### Challenge 5: Full CPU-only Docker Deployment of a Transformers Model
**Problem**: The K8s deployment's backend pods (1Gi memory limit) got OOMKilled on the very first analysis, because `SentimentMLAgent` downloaded the ~430MB FinBERT model from HuggingFace at runtime.
**Solution**: Two changes — raised the pod memory limit to 2Gi, and pre-downloaded FinBERT into the Docker image at *build* time so pods start with the model already cached, eliminating the runtime download entirely (and making cold starts deterministic).

---

## 🔍 Common Interview Questions & Answers

### Q1: Why 7 separate agents instead of one function that fetches everything?

**Answer**: "Independent failure isolation and independent testability. If the options chain provider is down, I still want fundamentals, technicals, and sentiment to complete — the Supervisor merges around a `failed` status instead of the whole analysis dying. It also means each agent has a narrow, mockable interface, so the test suite can simulate any single agent failing without touching the other six."

### Q2: Why hand this to an LLM at all instead of a rules engine?

**Answer**: "The quantitative side — RSI, IV, earnings proximity, the stock-vs-options score — is all deterministic and computed *before* the LLM ever sees it, specifically so the model isn't inventing numbers. What a rules engine can't do well is synthesize seven inputs into a plain-English, specific rationale a trader can act on ('IV at 32% vs a 20% historical average, with earnings in 4 days, favors a defined-risk options structure over outright stock') — that's a language-generation and reasoning task, not a lookup table. I use a tool-call schema, not free-text parsing, so the output is still structurally validated."

### Q3: How do you keep LLM costs under control?

**Answer**: "Three layers: a per-analysis model selector (Haiku through Opus/Fable), a system-prompt prompt-cache (`cache_control: ephemeral`) so the ~700-token system prompt isn't re-billed at full price every call, and a live cost comparison table that shows exactly what the chosen model cost versus every alternative — computed from the actual token usage of that specific run, including cache read/write tokens at their real rates."

### Q4: What happens if the LLM call fails or the model refuses?

**Answer**: "There's no silent fallback for a hard failure — it surfaces as a structured error to the caller rather than a degraded verdict, because a wrong stock recommendation is worse than a visible error. For Fable-tier models specifically, which run stricter safety classifiers, I opt into Anthropic's server-side refusal fallback so a policy decline gets re-served by Opus 4.8 within the same call — but I made sure cost/usage accounting attributes that request to whichever model *actually* served it, not the one originally requested, so billing stays accurate even when the fallback fires."

### Q5: How do you validate this actually works end-to-end, not just unit tests passing?

**Answer**: "A Playwright regression suite that runs a full live AAPL analysis through the real UI — all 7 agent cards rendering, the verdict streaming in, options metrics table populating — against both the Docker Compose deployment and the Kubernetes deployment, with the same checklist for both so I can catch environment-specific drift. It's 19 checks covering every page plus two live cross-symbol comparisons, run after every change that touches shared routing or backend logic."

### Q6: Docker Compose and Kubernetes — why both?

**Answer**: "Docker Compose is the fast local/single-host path. Kubernetes is there to prove the same application survives a more realistic deployment model — multiple backend/frontend replicas behind an Ingress, a StatefulSet for Postgres, rolling restarts with zero downtime. Building both forced me to fix real bugs Compose alone wouldn't have surfaced, like the Grafana provisioning `uid` mismatch and getting `kustomize`'s `configMapGenerator` to work with files outside the `k8s/` root."

### Q7: What was the most surprising bug you found?

**Answer**: "The model selector silently doing nothing on the streaming endpoint — the UI showed the user's chosen model, the analysis completed successfully, everything *looked* correct, and it was still wrong. I only caught it because I was specifically validating billing after adding a new model and saw the wrong model in the cost logs. It's a good example of why 'the feature appears to work' isn't the same as 'the feature works' — you need to verify the actual data path, not just the happy-path UI."

### Q8: How would you scale this to handle many more concurrent analyses?

**Answer**: "The backend is already horizontally scaled in K8s (2 replicas, stateless except for the DB), so adding replicas is straightforward. The bottleneck is external API rate limits (yfinance, LLM providers) rather than my own compute — I'd extend the existing TTL-cache + semaphore pattern already used for market quotes to more endpoints, and consider a request queue for the batch-analysis endpoint so a large universe scan doesn't starve interactive single-symbol requests."

---

## 🚀 Deployment

### Docker Compose
```bash
docker compose up -d        # postgres, redis, backend, frontend, nginx, prometheus, grafana
# Frontend → http://localhost:3010 (or http://stockresearch.local:8080 via nginx)
# API docs → http://localhost:8010/docs
```

### Kubernetes (Docker Desktop K8s, shown below — a non-Docker-Desktop cluster
### additionally needs the images loaded/pushed, since `imagePullPolicy: Never`
### assumes Docker Desktop's shared local image cache, plus an Ingress controller)
```powershell
.\k8s\build.ps1                      # builds stockresearch-backend:latest, stockresearch-frontend:k8s
kubectl create secret generic stockresearch-secret -n stockresearch \
  --from-literal=POSTGRES_PASSWORD=... --from-literal=DATABASE_URL=... \
  --from-literal=ANTHROPIC_API_KEY="$env:ANTHROPIC_API_KEY" ...   # kept out of git, applied imperatively
kubectl apply -k k8s\                # namespace, configmap, postgres, redis, backend, frontend, ingress
kubectl rollout status deployment/backend deployment/frontend -n stockresearch
# Frontend → http://app.stockresearch.local (Ingress) or NodePort 30300
# API      → http://api.stockresearch.local/docs or NodePort 30810
```

Both deployments are kept at feature parity and validated by the same regression checklist after every change.

---

## 📚 Project Structure

```
StockRecommendationPlatform/
├── app/
│   ├── agents/              # 7 specialist agents (market_data, fundamentals, technicals, ...)
│   ├── providers/           # yfinance / Polygon.io data provider layer
│   ├── services/
│   │   └── claude_service.py   # Multi-model LLM decision engine + cost accounting
│   ├── schemas/agents.py    # Pydantic contracts for every agent + SupervisorVerdict
│   ├── db/                  # SQLAlchemy models, Alembic migrations
│   ├── supervisor.py        # Orchestrates the 7 agents + decision support + LLM call
│   ├── decision_support.py  # Deterministic stock-vs-options scoring, checklist, sizing
│   ├── observability.py     # Prometheus instrumentator, correlation IDs
│   └── main.py               # FastAPI app, routers, middleware
├── frontend/src/
│   ├── app/                  # 15 Next.js pages (analysis, market-grid, momentum, ...)
│   ├── components/analysis/  # AnalysisForm, VerdictCard, ModelCostComparisonCard, ...
│   └── contexts/             # AnalysisContext (SSE), ApiKeyContext
├── k8s/                       # Kubernetes manifests + build.ps1
├── monitoring/                 # Prometheus + Grafana provisioning
├── tests/                      # 396 pytest tests
├── docker-compose.yml
├── launch.ps1                  # single-command local dev startup
├── README.md
└── Interview_Explanation.md    # This file
```

---

## 🎓 Skills Demonstrated

### Technical Skills
```
✅ Multi-agent async orchestration (asyncio.gather / wait(FIRST_COMPLETED))
✅ LLM tool-calling / structured outputs (Anthropic + OpenAI, multi-model)
✅ Prompt caching, refusal fallback handling, per-token cost accounting
✅ Real-time streaming (SSE for analysis, WebSocket for live price)
✅ FastAPI + async SQLAlchemy + Alembic + PostgreSQL
✅ Next.js 14 / TypeScript / Tailwind frontend
✅ Docker Compose + Kubernetes (StatefulSets, Ingress, rolling deploys)
✅ Observability: Prometheus, Grafana, OpenTelemetry, structlog
```

### Architectural Skills
```
✅ Separation of deterministic computation from LLM reasoning
✅ Failure-isolated multi-agent design (complete/degraded/failed per agent)
✅ Two-layer rate-limit mitigation (concurrency bound + TTL cache)
✅ Environment-parity validation (identical checklist, two deployment targets)
```

### Soft Skills / Process
```
✅ Debugging from a cost/billing anomaly back to a silent functional bug
✅ Acting on independent code review (multi-round accounting-correctness fixes)
✅ Writing regression tests that encode the exact bug being fixed, not just "it works"
```

---

## 💼 Closing Statement

*"This project demonstrates my ability to design a system where an LLM is used for exactly what it's good at — synthesizing structured evidence into a specific, actionable recommendation — while keeping every number it reasons over deterministic and pre-verified. It also shows production discipline: real-time streaming instead of blocking waits, cost transparency down to the token level, dual deployment targets validated in parity, and a habit of treating 'it looks like it works' as a hypothesis to verify, not a conclusion — which is exactly how I caught the silently-broken model selector.*

*I'm happy to go deeper into the agent design, the LLM cost-accounting logic, or the Docker/Kubernetes deployment story."*

---

## 📞 Follow-Up Topics

If the interviewer wants to go deeper, be ready to discuss:

- **Agent design**: how `AgentResultBase` standardizes status/provenance across all 7 agents
- **LLM integration**: the `submit_analysis_verdict` tool schema, adaptive thinking on Fable-tier models, prompt caching placement
- **Streaming**: SSE event framing on the backend, the fetch+ReadableStream parser on the frontend
- **Cost accounting**: the fallback-attribution bug and how a second review round caught two more accounting edge cases
- **Kubernetes**: Ingress domain routing, `configMapGenerator` constraints, StatefulSet for Postgres, zero-downtime rolling restarts
- **Testing strategy**: pytest fixtures that mock the LLM call entirely for deterministic supervisor tests, vs. the live Playwright suite for true end-to-end validation
- **Monitoring**: what's actually on the Grafana dashboard (service health, per-agent latency, batch job outcomes, resource usage)

---

*Document Version: 1.0*
*Last Updated: September 7, 2026*
*Project: Stock Recommendation Platform*
