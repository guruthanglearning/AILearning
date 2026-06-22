from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class AlertCondition(StrEnum):
    price_above = "price_above"
    price_below = "price_below"
    verdict_changes_to = "verdict_changes_to"


class ApiKeyCreate(BaseModel):
    name: str = Field(max_length=100)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
    key: str | None = None


class WatchlistCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime
    symbol_count: int = 0


class WatchlistSymbolAdd(BaseModel):
    symbol: str
    note: str | None = None


class WatchlistSymbolResponse(BaseModel):
    symbol: str
    note: str | None = None
    added_at: datetime


class AlertCreate(BaseModel):
    symbol: str
    condition: AlertCondition
    threshold_value: float | None = None
    threshold_verdict: str | None = None

    @model_validator(mode="after")
    def check_threshold(self) -> AlertCreate:
        if self.condition in (AlertCondition.price_above, AlertCondition.price_below):
            if self.threshold_value is None:
                raise ValueError("threshold_value required for price conditions")
        if self.condition == AlertCondition.verdict_changes_to:
            if not self.threshold_verdict:
                raise ValueError("threshold_verdict required for verdict_changes_to")
        return self


class AlertResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    condition: AlertCondition
    threshold_value: float | None = None
    threshold_verdict: str | None = None
    is_active: bool
    triggered_at: datetime | None = None
    created_at: datetime


class PortfolioPositionCreate(BaseModel):
    symbol: str = Field(max_length=20)
    shares: float = Field(gt=0)
    cost_basis: float = Field(gt=0)
    entry_date: date | None = None
    notes: str | None = None


class PortfolioPositionUpdate(BaseModel):
    shares: float | None = Field(default=None, gt=0)
    cost_basis: float | None = Field(default=None, gt=0)
    entry_date: date | None = None
    notes: str | None = None


class PortfolioPositionResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    shares: float
    cost_basis: float
    entry_date: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
