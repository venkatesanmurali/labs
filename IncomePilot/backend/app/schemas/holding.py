"""Pydantic v2 schemas for holdings."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class HoldingBase(BaseModel):
    symbol: str = Field(..., max_length=10, examples=["AAPL"])
    shares: int = Field(..., ge=1)
    avg_cost: float = Field(..., gt=0)
    owner: str = Field("Venky", pattern=r"^(Venky|Bharg)$")
    holding_type: str = Field("stock", pattern=r"^(stock|leaps)$")
    strike: Optional[float] = None
    expiry: Optional[str] = None
    option_type: Optional[str] = Field(None, pattern=r"^(call|put)$")
    tags: Optional[str] = Field(None, max_length=255)

    @model_validator(mode="after")
    def leaps_requires_fields(self):
        if self.holding_type == "leaps":
            if self.strike is None or self.expiry is None or self.option_type is None:
                raise ValueError(
                    "LEAPS holdings require strike, expiry, and option_type"
                )
        return self


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    symbol: Optional[str] = None
    shares: Optional[int] = Field(None, ge=1)
    avg_cost: Optional[float] = Field(None, gt=0)
    owner: Optional[str] = Field(None, pattern=r"^(Venky|Bharg)$")
    holding_type: Optional[str] = Field(None, pattern=r"^(stock|leaps)$")
    strike: Optional[float] = None
    expiry: Optional[str] = None
    option_type: Optional[str] = Field(None, pattern=r"^(call|put)$")
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
