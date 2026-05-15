from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_engine
from app.schemas.agents import AnalysisRunRequest, SupervisorVerdict
from app.supervisor import Supervisor


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    yield


app = FastAPI(
    title="Stock Recommendation Platform",
    description="Multi-agent research pipeline with decision aids (not investment advice).",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_supervisor = Supervisor()


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
