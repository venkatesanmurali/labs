"""View types for construction documents."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4

from app.domain.geometry import BoundingBox, Line2D, Point2D


class ViewType(Enum):
    FLOOR_PLAN = "floor_plan"
    RCP = "reflected_ceiling_plan"
    ELEVATION = "elevation"
    SECTION = "section"
    DETAIL = "detail"


class ElevationDirection(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass
class ViewScale:
    numerator: int = 1
    denominator: int = 100

    @property
    def factor(self) -> float:
        return self.numerator / self.denominator

    def __str__(self) -> str:
        return f"{self.numerator}:{self.denominator}"


@dataclass
class FloorPlanView:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Floor Plan"
    level_id: str = ""
    cut_height: float = 1.2  # meters above floor
    scale: ViewScale = field(default_factory=lambda: ViewScale(1, 100))
    bounds: Optional[BoundingBox] = None
    view_type: ViewType = ViewType.FLOOR_PLAN


@dataclass
class RCPView:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Reflected Ceiling Plan"
    level_id: str = ""
    scale: ViewScale = field(default_factory=lambda: ViewScale(1, 100))
    bounds: Optional[BoundingBox] = None
    view_type: ViewType = ViewType.RCP


@dataclass
class ElevationView:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Elevation"
    direction: ElevationDirection = ElevationDirection.NORTH
    level_id: str = ""
    scale: ViewScale = field(default_factory=lambda: ViewScale(1, 100))
    section_line: Optional[Line2D] = None
    height: float = 3.0  # total view height
    width: float = 10.0
    view_type: ViewType = ViewType.ELEVATION


@dataclass
class SectionView:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Section"
    cut_line: Optional[Line2D] = None
    level_id: str = ""
    scale: ViewScale = field(default_factory=lambda: ViewScale(1, 50))
    height: float = 3.0
    width: float = 10.0
    view_type: ViewType = ViewType.SECTION


@dataclass
class DetailView:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Detail"
    scale: ViewScale = field(default_factory=lambda: ViewScale(1, 20))
    bounds: Optional[BoundingBox] = None
    view_type: ViewType = ViewType.DETAIL
