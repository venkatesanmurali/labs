/* ── Holding ─────────────────────────────────────────────────────────── */
export interface Holding {
  id: number;
  symbol: string;
  shares: number;
  avg_cost: number;
  account_type: "taxable" | "retirement";
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface HoldingCreate {
  symbol: string;
  shares: number;
  avg_cost: number;
  account_type: string;
  tags?: string | null;
}

export interface CSVImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

/* ── Market Data ─────────────────────────────────────────────────────── */
export interface Quote {
  symbol: string;
  price: number;
  timestamp: string;
}

/* ── Recommendation ──────────────────────────────────────────────────── */
export interface CandidateMetrics {
  symbol: string;
  strike: number;
  expiry: string;
  dte: number;
  bid: number;
  ask: number;
  mid: number;
  premium_yield_pct: number;
  annualized_yield_pct: number;
  moneyness_pct: number;
  prob_itm_proxy: number;
  delta: number;
  iv: number;
  open_interest: number;
  volume: number;
  score: number;
  why: string;
  risk_note: string;
  income_note: string;
}

export interface RecommendationResponse {
  symbol: string;
  spot: number;
  strategy_type: "CC" | "CSP";
  earnings_warning: string | null;
  candidates: CandidateMetrics[];
}

/* ── Roll ─────────────────────────────────────────────────────────────── */
export interface RollRequest {
  symbol: string;
  strike: number;
  expiry: string;
  sold_price: number;
  current_option_mid: number;
  current_spot: number;
  days_to_expiry: number;
}

export interface RollAlternative {
  strike: number;
  expiry: string;
  dte: number;
  bid: number;
  ask: number;
  mid: number;
  delta: number;
  net_credit: number;
  new_moneyness_pct: number;
  explanation: string;
}

export interface RollDecision {
  action: string;
  explanation: string;
  current_extrinsic: number;
  current_intrinsic: number;
  alternatives: RollAlternative[];
}

/* ── Journal ─────────────────────────────────────────────────────────── */
export interface JournalEntry {
  id: number;
  symbol: string;
  decision_type: string;
  strike: number;
  expiry: string;
  premium: number;
  delta_at_entry: number | null;
  contracts: number;
  rationale: string | null;
  was_assigned: boolean | null;
  closed_price: number | null;
  profit: number | null;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryCreate {
  symbol: string;
  decision_type: string;
  strike: number;
  expiry: string;
  premium: number;
  delta_at_entry?: number | null;
  contracts?: number;
  rationale?: string | null;
}

/* ── Analytics ────────────────────────────────────────────────────────── */
export interface MonthlyPremium {
  month: string;
  total_premium: number;
  entry_count: number;
}

export interface DeltaBucket {
  bucket: string;
  count: number;
}

export interface PnLSummary {
  total_premium_collected: number;
  total_closed_cost: number;
  realized_pnl: number;
  open_positions: number;
  unrealized_estimate: number;
}

export interface AnalyticsDashboard {
  monthly_premiums: MonthlyPremium[];
  delta_distribution: DeltaBucket[];
  pnl: PnLSummary;
}

/* ── Strategy Config ──────────────────────────────────────────────────── */
export interface StrategyConfig {
  id: number;
  profile_name: string;
  target_delta_min: number;
  target_delta_max: number;
  preferred_dte_min: number;
  preferred_dte_max: number;
  min_annualized_yield: number;
  max_assignment_probability: number;
  avoid_earnings_before_days: number;
  avoid_earnings_after_days: number;
  min_open_interest: number;
  min_volume: number;
  w_yield: number;
  w_delta_fit: number;
  w_liquidity: number;
  w_distance: number;
  w_earnings_safety: number;
  roll_max_debit: number;
}
