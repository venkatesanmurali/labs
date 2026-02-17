"""Pydantic v2 schemas for strategy configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StrategyConfigBase(BaseModel):
    target_delta_min: float = Field(0.15, ge=0, le=1)
    target_delta_max: float = Field(0.30, ge=0, le=1)
    preferred_dte_min: int = Field(7, ge=1)
    preferred_dte_max: int = Field(21, ge=1)
    min_annualized_yield: float = Field(8.0, ge=0)
    max_assignment_probability: float = Field(35.0, ge=0, le=100)
    avoid_earnings_before_days: int = Field(7, ge=0)
    avoid_earnings_after_days: int = Field(2, ge=0)
    min_open_interest: int = Field(100, ge=0)
    min_volume: int = Field(10, ge=0)
    w_yield: float = Field(0.35, ge=0, le=1)
    w_delta_fit: float = Field(0.25, ge=0, le=1)
    w_liquidity: float = Field(0.20, ge=0, le=1)
    w_distance: float = Field(0.10, ge=0, le=1)
    w_earnings_safety: float = Field(0.10, ge=0, le=1)
    roll_max_debit: float = Field(0.50, ge=0)


class StrategyConfigUpdate(StrategyConfigBase):
    pass


class StrategyConfigOut(StrategyConfigBase):
    id: int
    profile_name: str

    model_config = {"from_attributes": True}
