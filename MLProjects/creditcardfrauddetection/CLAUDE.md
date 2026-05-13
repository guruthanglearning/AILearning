# Claude Code Configuration — Credit Card Fraud Detection

## Permissions & Approvals

### Auto-approved (no confirmation needed)
Claude may freely perform the following within `D:\Study\AILearning\MLProjects\creditcardfrauddetection\` **without asking for permission**:

- Read, edit, create, or delete any file inside this project directory
- Run tests (`pytest`, `python -m pytest`)
- Run linters and formatters (`ruff`, `black`, `isort`, `mypy`)
- Install or upgrade Python packages via pip into the shared environment
- Start or restart local dev servers (uvicorn API, Streamlit UI)
- Execute any script in `scripts/` or project root (`.py`, `.ps1`, `.sh`)
- Write or overwrite test files under `tests/`
- Update configuration files (`.env.*`, `Makefile`, `docker-compose*.yml`, `requirements*.txt`)
- Run `git status`, `git diff`, `git log`, `git add`, `git commit` (local commits only)
- Delete generated/temporary files: `__pycache__/`, `*.pyc`, `.coverage`, `htmlcov/`, `*.egg-info/`

### Require explicit user confirmation before proceeding
These actions affect shared or external systems and must be confirmed first:

- **Git destructive ops**: `git reset --hard`, `git push --force`, `git branch -D`, `git clean -f`
- **Publishing**: pushing to remote (`git push`), opening/closing/merging pull requests
- **Docker production**: deploying to production Docker or cloud environments
- **Secrets**: reading, editing, or committing any `.env` file that may contain real credentials
- **Database schema changes**: dropping tables, running irreversible migrations on shared data
- **Deleting files outside the project root**: anything outside `D:\Study\AILearning\MLProjects\creditcardfrauddetection\`
- **Sending external messages**: emails, Slack, webhooks, GitHub comments on issues/PRs
- **Dependency downgrades**: removing or downgrading packages that may break other projects in `shared_Environment`
- **Port changes**: changing default ports (8000/8501) in any config or script

---

## Project Overview

| Component | Technology | Port |
|-----------|-----------|------|
| API | FastAPI + uvicorn | 8000 |
| UI | Streamlit | 8501 |
| ML Model | XGBoost | — |
| LLM / RAG | LangChain + ChromaDB + HuggingFace | — |
| Vector DB | ChromaDB (in-process) | — |

---

## Environment

- Python: `D:\Study\AILearning\shared_Environment\Scripts\python.exe`
- pip: `D:\Study\AILearning\shared_Environment\Scripts\pip.exe`
- All packages live in `shared_Environment` — do **not** create a new venv
- Always use the full path to python/pip; do not rely on `python` or `pip` being on PATH

---

## Common Commands

```powershell
# Launch both API + UI (preferred)
.\start_all_services.ps1

# API only
D:\Study\AILearning\shared_Environment\Scripts\python.exe run_server.py

# UI only
D:\Study\AILearning\shared_Environment\Scripts\python.exe run_ui.py

# API docs (browser)
# http://localhost:8000/docs

# Restart API (use this script)
.\restart_api.ps1
```

```bash
# Lint
ruff check app/ tests/
ruff format app/ tests/

# Type check
mypy app/ --ignore-missing-imports

# Tests (unit + integration)
pytest tests/ --ignore=tests/test_ui_playwright.py --ignore=tests/test_ui_e2e.py -v

# Tests with coverage
pytest --cov=app --cov-report=term-missing tests/ --ignore=tests/test_ui_playwright.py

# E2E (requires live services on 8000 + 8501)
pytest tests/test_ui_playwright.py --browser chromium
```

---

## Key Architecture Notes

- `app/api/models/` (package) shadows `app/api/models.py` — actual Pydantic models are in `app/api/models_base.py`, re-exported via `app/api/models/__init__.py`
- Auth: `X-API-Key` header; dev key = `development_api_key_for_testing`; auth bypassed when `AUTH_REQUIRED=False`
- LLM fallback chain: OpenAI → Online Ollama → Local Ollama → Enhanced Mock
- `llm_service_type="local"` in health response does **not** mean Ollama is running — actual availability is checked at call time
- All API routes under `/api/v1/` prefix; `/predict` is an alias for `/detect-fraud`

---

## Code Style & Conventions

### General
- Follow PEP 8; max line length 100 characters
- Use type hints on all function signatures
- Prefer explicit over implicit — no magic values, no bare `except:`
- Do not add docstrings or comments to code you did not change

### Python / FastAPI
- Pydantic v2: use `@field_validator`, `@model_validator(mode='before')`, `model_config`
- All API routes live under `/api/v1/` prefix
- Use `BackgroundTasks` for async work; never block the request thread with LLM or embedding calls
- Log with the module-level logger: `logger = logging.getLogger(__name__)`
- Use `HTTPException` for all API errors; never let raw exceptions propagate

### Testing
- Mock all external I/O: `requests`, `HuggingFaceEmbeddings`, `SentenceTransformer`, `Chroma`, `subprocess`
- Use `patch()` as context managers or decorators — never leave real network calls in unit tests
- Use `LLMService.__new__(LLMService)` to bypass heavy `__init__` in LLM service tests
- One `assert` per test where practical; test names must describe the expected behaviour
- Minimum coverage target: **80%** overall; new modules must reach **70%** before merging

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `test_<module_name>.py`; test functions: `test_<behaviour>()`

---

## Git Workflow

- Branch naming: `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- Commit style: `<type>: <short summary>` — types: `feat`, `fix`, `test`, `refactor`, `chore`, `docs`
- Keep commits atomic — one logical change per commit
- Never commit directly to `main`; use a feature branch and PR
- Run tests locally before committing; CI must be green before merging
- Do not commit `.env`, `*.pyc`, `__pycache__/`, `htmlcov/`, or model binary files

---

## Security Practices

- All secrets via environment variables — never hardcode API keys, passwords, or tokens
- `.env` files are gitignored; `.env.example` (no real values) is the only env file committed
- API authentication via `X-API-Key` header — do not weaken or remove auth middleware
- Validate all user input at the API boundary (Pydantic handles this automatically)
- Do not log sensitive data (card numbers, full transaction amounts at DEBUG level in production)
- Keep dependencies up to date; run `pip check` after any dependency change

---

## Error Handling & Logging

- Always catch specific exceptions; avoid bare `except:` or `except Exception:` without re-raising or logging
- Log errors with `logger.error(..., exc_info=True)` to capture stack traces
- Return structured error responses using `ErrorResponse` model — never raw strings
- For LLM failures, fall back gracefully; never let LLM errors surface as 500s to the UI
- Use log levels correctly: `DEBUG` for tracing, `INFO` for normal ops, `WARNING` for degraded state, `ERROR` for failures

---

## Performance Guidelines

- LLM calls are slow (~5–30s) — always run them in `BackgroundTasks` or async workers
- Embedding model loads once at startup — do not reload `SentenceTransformer` per request
- ChromaDB is in-process — no separate service needed, but avoid large bulk inserts on the request path
- XGBoost inference is fast (<10ms) — safe to run synchronously in the request handler
- CLI subprocess fallback for Ollama has a **5-second timeout** — do not increase it

---

## Known Issues & Constraints (do not attempt to fix)

| Issue | Reason |
|-------|--------|
| `h11` version conflict (`httpcore` vs `wsproto`) | Irresolvable circular constraint; runtime works fine |
| `numpy 1.26.4` (langchain wants `>=2.1.0`) | Upgrading numpy breaks xgboost/scikit-learn in `shared_Environment` |
| FastAPI `on_event` deprecation warning | Requires lifespan refactor; low priority |
| LangChain `HuggingFaceEmbeddings`/`Chroma` deprecation | Needs `langchain-huggingface`/`langchain-chroma` migration; low priority |
| Ghost socket on port 8000 after unclean shutdown | Windows kernel artifact; clear by closing all terminals or rebooting |

---

## What NOT To Do

- Do not create new virtual environments — all packages go in `shared_Environment`
- Do not upgrade `numpy`, `xgboost`, `scikit-learn`, or `transformers` without explicit approval
- Do not add `time.sleep()` in request handlers — use async patterns
- Do not use `print()` in application code — use the logger
- Do not call OpenAI, Ollama, or any external LLM API in unit tests — mock them
- Do not add emojis to Python source files — Windows cp1252 console will fail to encode them
- Do not commit `restart_api.ps1` or `check_port.ps1` — they are temporary operational scripts
- Do not merge untested code — coverage must not drop below the current baseline
