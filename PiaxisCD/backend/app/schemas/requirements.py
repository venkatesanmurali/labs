"""Pydantic schemas for program requirements input."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RoomRequirementInput(BaseModel):
    name: str
    function: str = "custom"
    area: float = Field(..., gt=0)
    count: int = Field(1, ge=1)
    adjacencies: list[str] = []
    must_have_window: bool | None = None
    floor_finish: str = "Concrete"
    wall_finish: str = "Paint"
    ceiling_finish: str = "Gypsum"
    ceiling_height: float = 3.0


class DesignConstraintsInput(BaseModel):
    max_footprint_width: float = 30.0
    max_footprint_depth: float = 20.0
    min_corridor_width: float = 1.2
    min_door_width: float = 0.9
    default_wall_thickness: float = 0.2
    exterior_wall_thickness: float = 0.3
    floor_to_floor_height: float = 3.0


class RequirementsInput(BaseModel):
    rooms: list[RoomRequirementInput] = []
    constraints: DesignConstraintsInput = DesignConstraintsInput()
    notes: str = ""


class RequirementsTextInput(BaseModel):
    text: str = Field(..., min_length=1)
