"""Core geometry primitives for AEC domain."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator
from uuid import uuid4


@dataclass(frozen=True)
class Point2D:
    x: float = 0.0
    y: float = 0.0

    def distance_to(self, other: Point2D) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def midpoint(self, other: Point2D) -> Point2D:
        return Point2D((self.x + other.x) / 2, (self.y + other.y) / 2)

    def offset(self, dx: float, dy: float) -> Point2D:
        return Point2D(self.x + dx, self.y + dy)

    def __add__(self, other: Point2D) -> Point2D:
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point2D) -> Point2D:
        return Point2D(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class Point3D:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_2d(self) -> Point2D:
        return Point2D(self.x, self.y)


@dataclass(frozen=True)
class Line2D:
    start: Point2D
    end: Point2D

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def midpoint(self) -> Point2D:
        return self.start.midpoint(self.end)

    @property
    def direction(self) -> tuple[float, float]:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        ln = self.length
        if ln == 0:
            return (0.0, 0.0)
        return (dx / ln, dy / ln)

    @property
    def is_horizontal(self) -> bool:
        return abs(self.end.y - self.start.y) < 1e-6

    @property
    def is_vertical(self) -> bool:
        return abs(self.end.x - self.start.x) < 1e-6


@dataclass(frozen=True)
class BoundingBox:
    min_pt: Point2D
    max_pt: Point2D

    @property
    def width(self) -> float:
        return self.max_pt.x - self.min_pt.x

    @property
    def height(self) -> float:
        return self.max_pt.y - self.min_pt.y

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> Point2D:
        return self.min_pt.midpoint(self.max_pt)

    def contains(self, pt: Point2D) -> bool:
        return (self.min_pt.x <= pt.x <= self.max_pt.x and
                self.min_pt.y <= pt.y <= self.max_pt.y)

    def intersects(self, other: BoundingBox) -> bool:
        return not (self.max_pt.x < other.min_pt.x or
                    other.max_pt.x < self.min_pt.x or
                    self.max_pt.y < other.min_pt.y or
                    other.max_pt.y < self.min_pt.y)


class WallType(Enum):
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    PARTITION = "partition"
    SHEAR = "shear"


class DoorType(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SLIDING = "sliding"
    POCKET = "pocket"


class WindowType(Enum):
    FIXED = "fixed"
    CASEMENT = "casement"
    DOUBLE_HUNG = "double_hung"
    SLIDING = "sliding"


class OpeningSide(Enum):
    LEFT = "left"
    RIGHT = "right"
    BOTH = "both"


@dataclass
class Wall:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    start: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=Point2D)
    thickness: float = 0.2  # meters
    height: float = 3.0  # meters
    wall_type: WallType = WallType.INTERIOR

    @property
    def line(self) -> Line2D:
        return Line2D(self.start, self.end)

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)

    @property
    def is_exterior(self) -> bool:
        return self.wall_type == WallType.EXTERIOR


@dataclass
class Door:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    width: float = 0.9  # meters
    height: float = 2.1  # meters
    door_type: DoorType = DoorType.SINGLE
    swing_side: OpeningSide = OpeningSide.LEFT
    wall_id: str = ""
    host_room_id: str = ""
    target_room_id: str = ""

    @property
    def clearance_radius(self) -> float:
        return self.width


@dataclass
class Window:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    width: float = 1.2  # meters
    height: float = 1.5  # meters
    sill_height: float = 0.9  # meters above floor
    window_type: WindowType = WindowType.FIXED
    wall_id: str = ""
    room_id: str = ""


@dataclass
class Opening:
    """A generic opening in a wall (no door/window leaf)."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    position: Point2D = field(default_factory=Point2D)
    width: float = 1.0
    height: float = 2.4
    wall_id: str = ""
