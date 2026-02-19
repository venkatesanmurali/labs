"""Pydantic v2 schemas for market data."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Quote(BaseModel):
    symbol: str
    price: float
    timestamp: datetime


class OptionContract(BaseModel):
    """Single option contract in the chain."""

    symbol: str
    expiry: date
    strike: float
    option_type: str = "call"  # always call for covered-call workflow
    bid: float
    ask: float
    last: float
    mid: float = Field(description="(bid+ask)/2")
    iv: float = Field(description="Implied volatility as decimal, e.g. 0.35 = 35%")
    delta: float
    gamma: float
    theta: float
    vega: float = 0.0
    open_interest: int
    volume: int
    dte: int = Field(description="Days to expiration")


class OptionChain(BaseModel):
    symbol: str
    as_of: datetime
    spot: float
    contracts: List[OptionContract]


class EarningsDate(BaseModel):
    symbol: str
    next_earnings: Optional[date] = None
