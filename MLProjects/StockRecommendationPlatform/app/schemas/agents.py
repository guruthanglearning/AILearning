from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    complete = "complete"
    degraded = "degraded"
    failed = "failed"


class DataProvenance(BaseModel):
    source: str
    fetched_at_utc: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: float | None = None


class AgentResultBase(BaseModel):
    agent_name: str
    status: AgentStatus
    provenance: DataProvenance
    error_message: str | None = None
    raw_artifact: dict[str, Any] = Field(default_factory=dict)


class MarketDataOutput(AgentResultBase):
    last_price: float | None = None
    previous_close: float | None = None
    day_change_pct: float | None = None
    volume: int | None = None
    market_state: str | None = None


class FundamentalsOutput(AgentResultBase):
    company_name: str | None = None
    sector: str | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    revenue_growth: float | None = None


class TechnicalsOutput(AgentResultBase):
    sma_20: float | None = None
    sma_50: float | None = None
    rsi_14: float | None = None
    trend_hint: str | None = None


class FinancialsOutput(AgentResultBase):
    summary: str | None = None
    filing_url_hint: str | None = None


class OptionsOutput(AgentResultBase):
    atm_iv: float | None = None
    nearest_expiry: str | None = None
    chain_liquidity_hint: str | None = None
    implied_move_1d_pct: float | None = None


class OptionRight(str, Enum):
    call = "call"
    put = "put"


class OptionLegType(str, Enum):
    long = "long"
    short = "short"


class OptionLeg(BaseModel):
    right: OptionRight
    strike: float
    quantity_signed: int
    leg_type: OptionLegType


class OptionsMetricRow(BaseModel):
    template_id: str
    strategy_label: str
    expiration: str | None = None
    dte_at_analysis: int | None = None
    legs: list[OptionLeg] = Field(default_factory=list)
    net_debit_credit: float | None = None
    max_profit: float | None = None
    max_loss: float | None = None
    breakeven_prices: list[float] = Field(default_factory=list)
    underlying_at_analysis: float | None = None
    row_data_quality: str = "degraded"
    degraded_reasons: list[str] = Field(default_factory=list)
    disclaimer: str = "Hypothetical scenarios only; not investment advice."
    trend_alignment: str | None = None
    liquidity: str | None = None
    execution_quality: str | None = None
    risk_profile: str | None = None
    expected_move: str | None = None
    management_rules: str | None = None


class SentimentMLOutput(AgentResultBase):
    sentiment_score: float | None = None
    forecast_signal: str | None = None
    confidence_note: str | None = None


class RiskProOutput(AgentResultBase):
    earnings_days_away: int | None = None
    has_upcoming_earnings: bool = False
    checklist: list[dict[str, Any]] = Field(default_factory=list)


class InstrumentRecommendation(str, Enum):
    stock = "stock"
    options = "options"
    no_trade = "no_trade"
    insufficient_data = "insufficient_data"


class OptionsGuidance(BaseModel):
    strategy_family: str | None = None
    rationale_codes: list[str] = Field(default_factory=list)
    strike_guidance: str | None = None
    max_loss_scenario: str | None = None
    profit_targets_scenario: list[str] = Field(default_factory=list)
    disclaimer: str = "Hypothetical scenarios only; not investment advice."


class DataFreshness(BaseModel):
    quote_age_ms: int | None = None
    chain_age_ms: int | None = None
    fundamentals_as_of_note: str | None = None


class AgentContribution(BaseModel):
    agent_name: str
    status: AgentStatus
    headline: str
    detail: str | None = None


class DecisionChecklistItem(BaseModel):
    id: str
    label: str
    state: str
    weight: float = 1.0
    explanation: str


class InstrumentPlayRow(BaseModel):
    play_id: str
    label: str
    when_favored: str
    max_risk_profile: str
    capital_efficiency_note: str
    complexity: str


class VolatilityContext(BaseModel):
    regime: str
    atm_iv: float | None = None
    hv_20d_annualized: float | None = None
    iv_vs_hv_note: str | None = None
    implied_move_1d_pct: float | None = None


class PositionSizingHint(BaseModel):
    instrument_type: str
    note: str
    suggested_risk_budget_pct_range: tuple[float, float] = (0.5, 2.0)
    example_notional_at_1pct_portfolio: float | None = None


class DecisionAids(BaseModel):
    """Structured helpers for choosing stock vs options."""

    summary_headline: str
    stock_vs_options_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="-1 favors options structures, +1 favors plain stock",
    )
    checklist: list[DecisionChecklistItem] = Field(default_factory=list)
    instrument_plays: list[InstrumentPlayRow] = Field(default_factory=list)
    volatility: VolatilityContext | None = None
    position_sizing: list[PositionSizingHint] = Field(default_factory=list)
    comparison_matrix: dict[str, Any] = Field(default_factory=dict)
    user_questions: list[str] = Field(
        default_factory=list,
        description="Prompts the trader should answer before sizing a trade",
    )
    options_metrics_table: list[OptionsMetricRow] = Field(default_factory=list)


class SupervisorVerdict(BaseModel):
    instrument_recommendation: InstrumentRecommendation
    confidence_note: str
    options: OptionsGuidance | None = None
    agent_contributions: list[AgentContribution] = Field(default_factory=list)
    data_freshness: DataFreshness = Field(default_factory=DataFreshness)
    decision_aids: DecisionAids | None = None


class AnalysisRunRequest(BaseModel):
    symbol: str
    portfolio_value_usd: float | None = None
    max_risk_per_trade_pct: float | None = Field(
        default=None,
        ge=0.1,
        le=10.0,
        description="Optional; used for position-sizing hints only",
    )
    batch_job_id: uuid.UUID | None = None
