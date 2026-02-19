"""Pydantic v2 schemas for the roll decision engine."""

from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel, Field


class RollRequest(BaseModel):
    """User-supplied inputs describing the current short call."""

    symbol: str
    strike: float
    expiry: date
    sold_price: float = Field(description="Premium received when sold")
    current_option_mid: float = Field(description="Current mid price of the option")
    current_spot: float
    days_to_expiry: int


class RollAlternative(BaseModel):
    """A potential roll-to contract."""

    strike: float
    expiry: date
    dte: int
    bid: float
    ask: float
    mid: float
    delta: float
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    net_credit: float = Field(
        description="Positive = credit received; negative = debit paid"
    )
    new_moneyness_pct: float
    expected_pnl_if_flat: float = Field(
        default=0.0,
        description="Expected P&L if stock stays flat until expiry (theta decay estimate)",
    )
    gamma_risk_score: float = Field(
        default=0.0, description="0-1 gamma risk indicator"
    )
    explanation: str


class RollDecision(BaseModel):
    """The engine's recommended action + alternatives table."""

    action: str = Field(
        description="hold | close | roll_out | roll_up_and_out | accept_assignment"
    )
    explanation: str
    current_extrinsic: float
    current_intrinsic: float
    gamma_risk_score: float = Field(
        default=0.0, description="0-1 gamma risk for current position"
    )
    theta_remaining_pct: float = Field(
        default=0.0,
        description="Remaining theta as % of original premium",
    )
    alternatives: List[RollAlternative]
