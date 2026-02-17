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
    net_credit: float = Field(
        description="Positive = credit received; negative = debit paid"
    )
    new_moneyness_pct: float
    explanation: str


class RollDecision(BaseModel):
    """The engine's recommended action + alternatives table."""

    action: str = Field(
        description="hold | close | roll_out | roll_up_and_out | accept_assignment"
    )
    explanation: str
    current_extrinsic: float
    current_intrinsic: float
    alternatives: List[RollAlternative]
