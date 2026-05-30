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
  theta_edge: string | null;
  gamma_risk: string | null;
  credit_quality: string | null;
  rule_30pct: string | null;
  rule_60pct: string | null;
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
  user_answers: string[];
  options_metrics_table: OptionsMetricRow[];
}

export interface TechnicalsSnapshot {
  // Moving averages
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  ema_20: number | null;
  ema_200: number | null;
  // RSI
  rsi_7: number | null;
  rsi_14: number | null;
  rsi_200: number | null;
  // MACD 6/13
  macd_6_13: number | null;
  macd_6_13_signal: number | null;
  macd_6_13_hist: number | null;
  // Volume
  obv: number | null;
  obv_slope: number | null; // 20-day normalized slope: positive = accumulation, negative = distribution
  // Volatility
  atr_pct_14: number | null;
  atr_pct_50: number | null;
  // Range
  week_52_high: number | null;
  week_52_low: number | null;
  // Trend
  trend_hint: string | null;
}

export interface FundamentalsSnapshot {
  company_name: string | null;
  sector: string | null;
  market_cap: number | null;
  pe_ratio: number | null;
  forward_pe: number | null;
  revenue_growth: number | null;
}

export interface SupervisorVerdict {
  instrument_recommendation: InstrumentRecommendation;
  confidence_note: string;
  options: OptionsGuidance | null;
  agent_contributions: AgentContribution[];
  data_freshness: DataFreshness;
  decision_aids: DecisionAids | null;
  technicals: TechnicalsSnapshot | null;
  fundamentals: FundamentalsSnapshot | null;
  sentiment_headlines: string[];
  sentiment_forecast: string | null;
  sentiment_score: number | null;
  earnings_days_away: number | null;
  has_upcoming_earnings: boolean;
}

export interface PriceBar {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface PriceHistoryResponse {
  symbol: string;
  period: string;
  data: PriceBar[];
}

export interface PeerRow {
  symbol: string;
  name: string;
  price: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  forward_pe: number | null;
  ytd_return: number | null;
  sector: string | null;
}

export interface PeersResponse {
  symbol: string;
  sector: string | null;
  peers: PeerRow[];
}

export interface LiveQuote {
  symbol: string;
  pre_market: number | null;
  open_price: number | null;
  current: number | null;
  post_market: number | null;
  previous_close: number | null;
  day_change_pct: number | null;
  volume: number | null;
  market_state: string | null;
  fetched_at_utc: string;
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

// ─── Analysis history ─────────────────────────────────────────────────────────

export interface AnalysisHistoryItem {
  run_id: string;
  symbol: string;
  started_at: string;
  finished_at: string | null;
  instrument_recommendation: string | null;
  confidence_note: string | null;
  last_price: number | null;
  stock_vs_options_score: number | null;
  status: string;
}

// ─── Market grid ─────────────────────────────────────────────────────────────

export interface MarketQuoteRow {
  symbol: string;
  pre_mkt_price: number | null;
  pre_mkt_change: number | null;
  last_price: number | null;
  change: number | null;
  post_mkt_price: number | null;
  post_mkt_change: number | null;
  earnings_date: string | null;
  market_cap: number | null;
  div_payment_date: string | null;
  exchange: string | null;
  week_52_high: number | null;
  week_52_low: number | null;
  shares_outstanding: number | null;
  fetched_at_utc: string;
}

// ─── Error log ───────────────────────────────────────────────────────────────

export interface ErrorLogEntry {
  ts: string;
  symbol: string;
  agent: string;
  status: string;
  message: string;
}

// ─── SSE streaming event types ───────────────────────────────────────────────

export interface SseAgentDoneEvent {
  type: "agent_done";
  agent: string;
  status: AgentStatus;
  headline: string;
  detail: string | null;
}

export interface SseVerdictEvent {
  type: "verdict";
  data: SupervisorVerdict;
}

export type SseEvent =
  | SseAgentDoneEvent
  | SseVerdictEvent
  | { type: "done" }
  | { type: "error"; message: string };

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
