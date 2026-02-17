"""Pydantic v2 schemas for the trade journal."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JournalEntryBase(BaseModel):
    symbol: str = Field(..., max_length=10)
    decision_type: str = Field(
        ..., pattern=r"^(sell|close|roll|hold|assign)$"
    )
    strike: float
    expiry: str  # YYYY-MM-DD
    premium: float = 0.0
    delta_at_entry: Optional[float] = None
    contracts: int = 1
    rationale: Optional[str] = None
    was_assigned: Optional[bool] = None
    closed_price: Optional[float] = None
    profit: Optional[float] = None


class JournalEntryCreate(JournalEntryBase):
    pass


class JournalEntryUpdate(BaseModel):
    was_assigned: Optional[bool] = None
    closed_price: Optional[float] = None
    profit: Optional[float] = None
    rationale: Optional[str] = None


class JournalEntryOut(JournalEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
