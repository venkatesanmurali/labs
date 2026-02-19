"""Pydantic v2 schemas for covered-call recommendations."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateMetrics(BaseModel):
    """Computed metrics for a single covered-call candidate."""

    symbol: str
    strike: float
    expiry: date
    dte: int
    bid: float
    ask: float
    mid: float

    # ── Computed metrics ──────────────────────────────────────────────────
    # premium_yield_pct = mid / (spot * 100) — yield per contract as % of stock
    premium_yield_pct: float = Field(
        description="premium / (spot price) as percentage"
    )
    # annualized_yield_pct = premium_yield_pct * (365 / dte)
    annualized_yield_pct: float
    # moneyness_pct = (strike - spot) / spot
    moneyness_pct: float
    # prob_itm_proxy = abs(delta)
    prob_itm_proxy: float
    delta: float
    iv: float
    vega: float = 0.0
    spread_width: float = 0.0
    theta_daily_dollar: float = 0.0
    open_interest: int
    volume: int

    # ── Composite score ───────────────────────────────────────────────────
    score: float = Field(description="Weighted composite 0-100")

    # ── Explanation ───────────────────────────────────────────────────────
    why: str = Field(description="Human-readable reason for this pick")
    risk_note: str
    income_note: str


class RecommendationResponse(BaseModel):
    symbol: str
    spot: float
    strategy_type: str = Field(default="CC", description="CC (Covered Call) or CSP (Cash Secured Put)")
    earnings_warning: Optional[str] = None
    candidates: List[CandidateMetrics]
