// TypeScript interfaces mirroring the backend Pydantic schemas.
// Source of truth: app/schemas/agents.py, app/schemas/user.py, app/schemas/batch.py

// ─── Enums ───────────────────────────────────────────────────────────────────

export type AgentStatus = "complete" | "degraded" | "failed";
export type InstrumentRecommendation = "stock" | "options" | "no_trade" | "insufficient_data";
export type OptionRight = "call" | "put";
export type OptionLegType = "long" | "short";
export type AlertCondition = "price_above" | "price_below" | "verdict_changes_to";
export type BatchJobStatus = "pending" | "running" | "complete" | "partial" | "failed";
export type DataQuality = "full" | "partial" | "degraded";

// ─── Analysis schemas ─────────────────────────────────────────────────────────

export interface DataProvenance {
  source: string;
  fetched_at_utc: string;
  latency_ms: number | null;
}

export interface OptionLeg {
  right: OptionRight;
  strike: number;
  quantity_signed: number;
  leg_type: OptionLegType;
}

export interface OptionsMetricRow {
  template_id: string;
  strategy_label: string;
  expiration: string | null;
  dte_at_analysis: number | null;
  legs: OptionLeg[];
  net_debit_credit: number | null;
  max_profit: number | null;
  max_loss: number | null;
  breakeven_prices: number[];
  underlying_at_analysis: number | null;
  row_data_quality: DataQuality;
  degraded_reasons: string[];
  disclaimer: string;
  trend_alignment: string | null;
  liquidity: string | null;
  execution_quality: string | null;
  risk_profile: string | null;
  expected_move: string | null;
  management_rules: string | null;
}

export interface OptionsGuidance {
  strategy_family: string | null;
  rationale_codes: string[];
  strike_guidance: string | null;
  max_loss_scenario: string | null;
  profit_targets_scenario: string[];
  disclaimer: string;
}

export interface DataFreshness {
  quote_age_ms: number | null;
  chain_age_ms: number | null;
  fundamentals_as_of_note: string | null;
}

export interface AgentContribution {
  agent_name: string;
  status: AgentStatus;
  headline: string;
  detail: string | null;
}

export interface DecisionChecklistItem {
  id: string;
  label: string;
  state: string;
  weight: number;
  explanation: string;
}

export interface InstrumentPlayRow {
  play_id: string;
  label: string;
  when_favored: string;
  max_risk_profile: string;
  capital_efficiency_note: string;
  complexity: string;
}

export interface VolatilityContext {
  regime: string;
  atm_iv: number | null;
  hv_20d_annualized: number | null;
  iv_vs_hv_note: string | null;
  implied_move_1d_pct: number | null;
}

export interface PositionSizingHint {
  instrument_type: string;
  note: string;
  suggested_risk_budget_pct_range: [number, number];
  example_notional_at_1pct_portfolio: number | null;
}

export interface DecisionAids {
  summary_headline: string;
  stock_vs_options_score: number;
  checklist: DecisionChecklistItem[];
  instrument_plays: InstrumentPlayRow[];
  volatility: VolatilityContext | null;
  position_sizing: PositionSizingHint[];
  comparison_matrix: Record<string, unknown>;
  user_questions: string[];
  options_metrics_table: OptionsMetricRow[];
}

export interface SupervisorVerdict {
  instrument_recommendation: InstrumentRecommendation;
  confidence_note: string;
  options: OptionsGuidance | null;
  agent_contributions: AgentContribution[];
  data_freshness: DataFreshness;
  decision_aids: DecisionAids | null;
}

export interface AnalysisRunRequest {
  symbol: string;
  portfolio_value_usd?: number | null;
  max_risk_per_trade_pct?: number | null;
}

// ─── Batch schemas ────────────────────────────────────────────────────────────

export interface BatchJobRequest {
  universe: "top10" | "top100" | "full" | "custom";
  symbols?: string[] | null;
  portfolio_value_usd?: number | null;
  max_risk_per_trade_pct?: number | null;
  batch_key?: string | null;
}

export interface BatchSymbolResult {
  symbol: string;
  verdict: InstrumentRecommendation | null;
  error: string | null;
}

export interface BatchJobResponse {
  job_id: string;
  status: BatchJobStatus;
  universe: string;
  total_symbols: number;
  completed_symbols: number;
  failed_symbols: number;
  composition_as_of: string | null;
  results: BatchSymbolResult[];
  requested_at: string | null;
  finished_at: string | null;
}

// ─── Auth / API Key schemas ───────────────────────────────────────────────────

export interface ApiKeyCreate {
  name: string;
}

export interface ApiKeyResponse {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  key: string | null;
}

// ─── Watchlist schemas ────────────────────────────────────────────────────────

export interface WatchlistCreate {
  name: string;
  description?: string | null;
}

export interface WatchlistResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  symbol_count: number;
}

export interface WatchlistSymbolAdd {
  symbol: string;
  note?: string | null;
}

export interface WatchlistSymbolResponse {
  symbol: string;
  note: string | null;
  added_at: string;
}

// ─── Alert schemas ────────────────────────────────────────────────────────────

export interface AlertCreate {
  symbol: string;
  condition: AlertCondition;
  threshold_value?: number | null;
  threshold_verdict?: string | null;
}

export interface AlertResponse {
  id: string;
  symbol: string;
  condition: AlertCondition;
  threshold_value: number | null;
  threshold_verdict: string | null;
  is_active: boolean;
  triggered_at: string | null;
  created_at: string;
}
