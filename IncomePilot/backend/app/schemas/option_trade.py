"""Pydantic v2 schemas for option trades."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OptionTradeCreate(BaseModel):
    symbol: str = Field(..., max_length=10)
    strategy_type: str = Field(..., pattern=r"^(CC|CSP|STOCK)$")
    trade_type: str = Field(..., pattern=r"^(fresh|roll|sell)$")
    strike: Optional[float] = Field(None, gt=0)  # sell price for STOCK, strike for options
    expiry: Optional[datetime] = None  # not needed for STOCK
    premium: float  # can be negative (loss/buyback); for STOCK = (sell - avg_cost) * shares
    contracts: float = Field(1, ge=0)  # fractional shares for STOCK
    trade_date: date
    owner: str = Field("Venky", pattern=r"^(Venky|Bharg)$")
    notes: Optional[str] = None
    avg_cost: Optional[float] = None  # for STOCK: buy price per share (frontend calc only)


class OptionTradeUpdate(BaseModel):
    notes: Optional[str] = None
    premium: Optional[float] = None
    trade_type: Optional[str] = Field(None, pattern=r"^(fresh|roll|sell)$")


class OptionTradeOut(BaseModel):
    id: int
    symbol: str
    strategy_type: str
    trade_type: str
    strike: Optional[float]
    expiry: Optional[datetime]
    premium: float
    contracts: float
    trade_date: date
    owner: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TradeCSVImportResult(BaseModel):
    imported: int
    skipped: int
    errors: List[str]
