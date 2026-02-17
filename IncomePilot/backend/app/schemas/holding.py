"""Pydantic v2 schemas for holdings."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HoldingBase(BaseModel):
    symbol: str = Field(..., max_length=10, examples=["AAPL"])
    shares: int = Field(..., ge=1)
    avg_cost: float = Field(..., gt=0)
    account_type: str = Field("taxable", pattern=r"^(taxable|retirement)$")
    tags: Optional[str] = Field(None, max_length=255)


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    symbol: Optional[str] = None
    shares: Optional[int] = Field(None, ge=1)
    avg_cost: Optional[float] = Field(None, gt=0)
    account_type: Optional[str] = Field(None, pattern=r"^(taxable|retirement)$")
    tags: Optional[str] = None


class HoldingOut(HoldingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CSVImportResult(BaseModel):
    imported: int
    skipped: int
    errors: List[str]
