"""Pydantic v2 schemas for option trades."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OptionTradeCreate(BaseModel):
    symbol: str = Field(..., max_length=10)
    strategy_type: str = Field(..., pattern=r"^(CC|CSP)$")
    trade_type: str = Field(..., pattern=r"^(fresh|roll)$")
    strike: float = Field(..., gt=0)
    expiry: str = Field(...)  # YYYY-MM-DD
    premium: float  # can be negative (loss/buyback)
    contracts: int = Field(1, ge=1)
    trade_date: date
    owner: str = Field("Venky", pattern=r"^(Venky|Bharg)$")
    notes: Optional[str] = None


class OptionTradeUpdate(BaseModel):
    notes: Optional[str] = None
    premium: Optional[float] = None
    trade_type: Optional[str] = Field(None, pattern=r"^(fresh|roll)$")


class OptionTradeOut(BaseModel):
    id: int
    symbol: str
    strategy_type: str
    trade_type: str
    strike: float
    expiry: str
    premium: float
    contracts: int
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
