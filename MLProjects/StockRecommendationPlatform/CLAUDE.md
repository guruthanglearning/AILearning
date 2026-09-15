# StockRecommendationPlatform — Claude Instructions

## What this is

A multi-agent stock research platform: 7 specialist agents + a Supervisor (FastAPI backend, Python 3.12) produce a stock-vs-options recommendation, served to a Next.js 14 / TypeScript frontend over SSE + a WebSocket live-price relay, backed by PostgreSQL (+ optional Redis cache). Runnable locally via `launch.ps1`, in Docker via `docker-compose.yml`, or in Kubernetes via `k8s/`. `README.md` has the full architecture diagrams, complete API reference, and page-by-page UI guide — this file covers what's needed to work in the code, including things not in the README.

## Commands

### Local dev — single command (recommended)
```powershell
cd D:\Study\AILearning\MLProjects\StockRecommendationPlatform
copy .env.example .env   # fill in ANTHROPIC_API_KEY at minimum
.\launch.ps1              # backend :8024 + frontend :3001; auto-syncs frontend .env.local port; opens browser
```

### Local dev — manual (run pieces separately)
```powershell
docker compose up -d postgres redis                          # infra only
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8024    # backend
cd frontend && npm install && npm run dev -- --port 3001       # frontend; plain `npm run dev` defaults to :3000, not :3001
```

### Tests & lint
```powershell
pytest -q                                    # full suite
pytest -q --cov=app --cov-report=term-missing
pytest tests/test_agents.py -v               # single file
pytest tests/test_agents.py::test_market_data_agent_complete -v   # single test
ruff check app/ tests/                       # lint (config: pyproject.toml)
```

### Docker — full stack (Postgres + Redis + backend + frontend + nginx)
```powershell
.\scripts\add_hosts.ps1     # one-time: adds stockresearch.local / api.stockresearch.local / grafana.../prometheus... to hosts file
docker compose up -d --build
docker compose up -d --force-recreate app   # after editing .env — compose does not hot-reload env vars into a running container
```
Access via **http://stockresearch.local:8080** (nginx-routed). The frontend image bakes `NEXT_PUBLIC_API_URL=http://api.stockresearch.local:8080` in at *build* time, so loading the UI at the direct port (`localhost:3010`) will fail to reach the API unless the hosts entries from `add_hosts.ps1` exist.

### Kubernetes (Docker Desktop K8s or kind)
```powershell
.\k8s\build.ps1                                     # builds stockresearch-backend:latest + stockresearch-frontend:k8s
kubectl apply -f k8s\namespace.yaml                 # must precede the secret/kustomize apply — apply -f doesn't auto-create the namespace (unlike apply -k)
Copy-Item k8s\secret.yaml.example k8s\secret.yaml   # fill in real keys — gitignored, never commit
kubectl apply -f k8s\secret.yaml
kubectl apply -k k8s\
```
Frontend: `localhost:30300`. Backend docs: `localhost:30810/docs`.

**Port schemes differ by environment on purpose** — local dev is 8024/3001, Docker Compose is 8010/3010 behind nginx on 8080, Kubernetes is NodePorts 30810/30300. Don't assume one applies elsewhere.

## Architecture

**Request flow:** rate limiter (slowapi) → `Supervisor.stream_analysis()` (`app/supervisor.py`) fires all 7 agents concurrently via `asyncio.create_task` × 7; `asyncio.wait(FIRST_COMPLETED)` emits an SSE `agent_done` event as each agent finishes individually, not batched → once all 7 complete, `decision_support.py`'s `build_decision_aids()` scores stock-vs-options → the result plus **6 of the 7** agent outputs (`market_data`, `fundamentals`, `technicals`, `options`, `risk_pro`, `sentiment_ml` — `financials` is computed and displayed/persisted but is *not* passed into `get_claude_verdict()`) are fed as structured context to a Claude LLM call → `_validate_strike_guidance()` in `supervisor.py` cross-checks the LLM's proposed options strikes against real chain data before trusting them, stamping `chain_validated` → persisted to Postgres (one `analysis_run` row + one `agent_artifact` row per agent) → final SSE `verdict` + `done` events. Note: the analysis endpoints (`/v1/analysis/run`, `/v1/analysis/stream/{symbol}`) are rate-limited only, not `X-API-Key`-gated — API-key auth (`get_current_key` in `app/auth.py`, SHA-256 hash via `hashlib`, not bcrypt) is enforced on the `watchlists`, `alerts`, `portfolio`, `settings`, and `auth` routers instead.

**The 7 agents** (`app/agents/`): `market_data.py`, `fundamentals.py`, `technicals.py` (SMA/EMA/RSI/MACD/ATR/OBV), `financials.py`, `options.py` (ATM IV, chain liquidity), `risk_pro.py` (earnings-window flag), `sentiment_ml.py` (fetches headlines from Finnhub — needs `FINNHUB_API_KEY` — then scores them locally with `ProsusAI/finbert`). All inherit generic `BaseAgent`/`safe_run()` from `app/agents/base.py` — a failed or timed-out agent (`AGENT_TIMEOUT_SECONDS`, default 45s) degrades to `status: failed` rather than aborting the whole run; downstream scoring still runs with fewer inputs rather than erroring out.

**Data providers** (`app/providers/`): `factory.py`'s `build_provider()` picks yfinance (default) or Polygon.io (if `POLYGON_API_KEY` is set), optionally wrapped in the `RedisCache` provider class (`redis_cache.py`) when `USE_REDIS=true`. `yfinance_provider.py` gates all calls behind a module-level `asyncio.Semaphore(3)` — yfinance isn't safe for unbounded concurrent calls, so don't remove that when touching this file.

**LLM model selection** (`app/services/claude_service.py`): the analysis model is chosen per-request from the UI, not hardcoded — `DEFAULT_MODEL = "claude-opus-4-8"`. `claude-fable-5` and `claude-fable-5-1` carry an automatic fallback to `claude-opus-4-8` (`extra_body.fallbacks`) if the Fable call fails; other models don't have this fallback.

**Live prices**: the Analysis page opens `/v1/ws/quote/{symbol}`, a WebSocket relay (`app/polygon_ws.py`) to Polygon's `wss://delayed.polygon.io/stocks` feed — requires `POLYGON_API_KEY`; without it, or on disconnect, the frontend falls back to HTTP REST polling.

**Database** (`app/db/models.py`, migrated via `alembic/versions/0001`–`0005`): `api_key` → `watchlist` → `watchlist_symbol` and `api_key` → `alert` are independent 1:N chains; `batch_job` → `analysis_run` → `agent_artifact` is the analysis-pipeline persistence chain (a single ad-hoc analysis has no `batch_job` row, only bulk/batch runs do).

**Frontend** (`frontend/src/`): `lib/api.ts` centralizes all fetch calls including `streamAnalysis()`'s SSE parsing; `contexts/AnalysisContext.tsx` holds the streaming state (`partialContributions`, `verdict`) that `AgentStatusGrid`/`VerdictCard`/etc. read from rather than each component managing its own SSE connection. The `/docs` page (`components/docs/ReadmeViewer.tsx`) fetches and renders this project's own `README.md` live from the backend (`GET /v1/docs/readme`) — so README changes are visible in the running app immediately, and factual errors in README are user-facing, not just a docs problem.

**Present in the code but not listed in README's "Project Structure" tree:** `app/services/` (`claude_service.py` — the model registry/pricing/fallback logic above), `app/error_log.py` (backs `GET/DELETE /v1/logs/errors` and the `/logs` page, wired directly in `main.py` rather than a router module), and `app/polygon_ws.py` (the WebSocket relay above).

## Pull Request & Code Review Workflow

Follows the workspace-wide policy in the root `D:\Study\AILearning\CLAUDE.md` (Pull Request & Code Review Workflow section): every change — code or documentation (`*.md`) — goes to a feature branch, opens a PR, gets reviewed by the Codex CLI (`codex exec`, non-interactive), has every finding addressed with a reply on its comment thread, gets re-reviewed, and only then merges. Do not push directly to `main`. See PRs #1–#5 on this repo for the established pattern (model additions, cost-comparison feature, saved-report lookups, the Interview_Explanation.md doc).

## CI/CD Policy

After every `git push`, always validate CI/CD without being asked:

1. Run `gh run list --limit 3 --repo guruthanglearning/AILearning` to get the latest run ID
2. Run `gh run watch <run-id> --repo guruthanglearning/AILearning` and wait for it to complete
3. If it **passes**: report "CI passed" and the run duration
4. If it **fails**: fetch the failed step logs with `gh run view <run-id> --repo guruthanglearning/AILearning --log-failed`, identify the root cause, fix it, commit, and push again
