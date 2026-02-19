"""Annotation elements for construction documents."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from app.domain.geometry import Line2D, Point2D


class DimensionStyle(Enum):
    LINEAR = "linear"
    ALIGNED = "aligned"
    ANGULAR = "angular"
    RADIAL = "radial"


@dataclass
class Dimension:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    start: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=Point2D)
    offset: float = 0.5  # distance from measured line
    value: float = 0.0  # actual dimension value in meters
    text_override: str = ""
    style: DimensionStyle = DimensionStyle.LINEAR
    layer: str = "A-DIMS"

    def __post_init__(self):
        if self.value == 0.0:
            self.value = self.start.distance_to(self.end)


@dataclass
class Tag:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    text: str = ""
    element_id: str = ""  # ID of tagged element
    layer: str = "A-ANNO-TAG"
    rotation: float = 0.0


@dataclass
class RoomTag:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    room_name: str = ""
    room_number: str = ""
    area: float = 0.0
    layer_name: str = "A-ROOM-NAME"
    layer_area: str = "A-ROOM-AREA"
    layer_number: str = "A-ROOM-NUMB"


@dataclass
class Callout:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    target_sheet: str = ""
    target_view: str = ""
    label: str = ""
    layer: str = "A-ANNO"


@dataclass
class NorthArrow:
    position: Point2D = field(default_factory=Point2D)
    rotation: float = 0.0  # degrees from true north
    size: float = 1.0


@dataclass
class ScaleBar:
    position: Point2D = field(default_factory=Point2D)
    scale_text: str = "1:100"
    length: float = 5.0  # bar length in drawing units
    divisions: int = 5


@dataclass
class ElevationMarker:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    direction: str = "N"
    target_sheet: str = ""
    target_view: str = ""
    layer: str = "A-ELEV-IDEN"


@dataclass
class SectionMarker:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    cut_line: Line2D = field(default_factory=lambda: Line2D(Point2D(), Point2D(1, 0)))
    label: str = "A"
    target_sheet: str = ""
    target_view: str = ""
    layer: str = "A-SECT-IDEN"
