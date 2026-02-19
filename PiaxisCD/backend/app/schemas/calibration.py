"""Pydantic schemas for image calibration."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CalibrationInput(BaseModel):
    input_ref_id: str
    pixel_distance: float = Field(..., gt=0)
    real_distance: float = Field(..., gt=0)
    unit: str = "meters"


class CalibrationResponse(BaseModel):
    input_ref_id: str
    scale_factor: float
    unit: str
