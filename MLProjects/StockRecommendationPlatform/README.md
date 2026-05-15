# Stock Recommendation Platform

Production-oriented **research** API: specialist agents (market data, fundamentals, technicals, financials, options, risk workflow, optional ML via StockPrediction) run in parallel; a **supervisor** returns a **stock vs options** umbrella recommendation plus **`decision_aids`** to support your own judgment.

**Not investment advice.** Data defaults to Yahoo Finance via `yfinance` (delay / breakage possible). For live production, swap in a commercial market-data vendor and wire Redis ingest as described in [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md).

## Decision-support extras (stock vs options)

Each analysis response includes `decision_aids`:

- **`stock_vs_options_score`**: heuristic in \([-1, 1]\); positive leans plain stock, negative leans options structures.
- **`checklist`**: directional clarity, earnings window, options liquidity, vol regime vs structure, optional ML vs technicals alignment.
- **`instrument_plays`**: when long stock, long call, debit vertical, or cash-secured put / covered call tends to fit.
- **`volatility`**: ATM IV, 20d realized vol proxy, IV vs HV note, implied move from ATM straddle mid (rough).
- **`comparison_matrix`**: risk axes plus **breakeven thinking** prompts.
- **`position_sizing`**: optional hints if you pass `portfolio_value_usd` and `max_risk_per_trade_pct`.
- **`user_questions`**: prompts to answer before committing capital.

## Run locally

```powershell
cd d:\Study\AILearning\MLProjects\StockRecommendationPlatform
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

- `GET http://127.0.0.1:8010/healthz`
- `GET http://127.0.0.1:8010/v1/analysis/run/AAPL?portfolio_value_usd=250000&max_risk_per_trade_pct=1`
- `POST http://127.0.0.1:8010/v1/analysis/run` with JSON body `{"symbol": "MSFT", "portfolio_value_usd": 100000, "max_risk_per_trade_pct": 0.5}`

### Optional: StockPrediction ML agent

If [StockPrediction](d:\Study\AILearning\MLProjects\StockPrediction) API is running on port 8000:

```powershell
set STOCK_PREDICTION_API_URL=http://127.0.0.1:8000
```

Then `SentimentMLAgent` calls `POST /stock_analysis` and feeds the **ML vs technicals** checklist when a non-Hold signal exists.

## Tests

```powershell
pytest -q
```

## Docker (Postgres + Redis only)

```powershell
docker compose up -d
```

Application code does not require these services yet for the MVP analysis path; they are placeholders for persistence and quote cache.
