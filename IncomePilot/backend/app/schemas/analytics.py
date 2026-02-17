"""Pydantic v2 schemas for analytics endpoints."""

from __future__ import annotations

from typing import List

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
