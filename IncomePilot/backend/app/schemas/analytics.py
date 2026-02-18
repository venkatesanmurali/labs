"""Pydantic v2 schemas for analytics endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class MonthlyPremium(BaseModel):
    month: str  # "YYYY-MM"
    total_premium: float
    entry_count: int


class DeltaBucket(BaseModel):
    bucket: str  # e.g. "0.10-0.15"
    count: int


class PnLSummary(BaseModel):
    total_premium_collected: float
    total_closed_cost: float
    realized_pnl: float
    open_positions: int
    unrealized_estimate: float


class AnalyticsDashboard(BaseModel):
    monthly_premiums: List[MonthlyPremium]
    delta_distribution: List[DeltaBucket]
    pnl: PnLSummary


# ── Income & Net Worth ────────────────────────────────────────────────────


class MonthlyIncome(BaseModel):
    month: str  # "YYYY-MM"
    cc_income: float
    csp_income: float
    total_income: float
    trade_count: int


class IncomeReport(BaseModel):
    start_date: str
    end_date: str
    monthly_breakdown: List[MonthlyIncome]
    totals: Dict[str, float]  # cc_total, csp_total
    grand_total: float


class YTDPnL(BaseModel):
    total_premium_collected: float
    total_losses: float
    net_pnl: float
    trade_count: int


class NetWorthHolding(BaseModel):
    symbol: str
    owner: str
    holding_type: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    pct_of_total: float


class NetWorthSummary(BaseModel):
    total_net_worth: float
    holdings: List[NetWorthHolding]
    by_owner: Dict[str, float]
