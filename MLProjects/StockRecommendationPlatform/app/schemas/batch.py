from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.agents import InstrumentRecommendation


class BatchJobStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    partial = "partial"
    failed = "failed"


class BatchJobRequest(BaseModel):
    universe: str = Field("top10", description="top10 | top100 | full | custom")
    symbols: list[str] | None = None
    portfolio_value_usd: float | None = None
    max_risk_per_trade_pct: float | None = Field(
        default=None, ge=0.1, le=10.0
    )
    batch_key: str | None = None


class BatchSymbolResult(BaseModel):
    symbol: str
    verdict: InstrumentRecommendation | None = None
    error: str | None = None


class BatchJobResponse(BaseModel):
    job_id: uuid.UUID
    status: BatchJobStatus
    universe: str
    total_symbols: int
    completed_symbols: int
    failed_symbols: int
    composition_as_of: str | None = None
    results: list[BatchSymbolResult] = Field(default_factory=list)
    requested_at: datetime | None = None
    finished_at: datetime | None = None
