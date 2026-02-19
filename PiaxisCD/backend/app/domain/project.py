"""Project hierarchy: Project → Site → Building → Level → Room/Zone."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4

from app.domain.geometry import BoundingBox, Door, Opening, Point2D, Wall, Window


class RoomFunction(Enum):
    BEDROOM = "bedroom"
    LIVING = "living"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    DINING = "dining"
    OFFICE = "office"
    STORAGE = "storage"
    CORRIDOR = "corridor"
    LOBBY = "lobby"
    STAIRCASE = "staircase"
    UTILITY = "utility"
    MECHANICAL = "mechanical"
    GARAGE = "garage"
    CUSTOM = "custom"


@dataclass
class Room:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    function: RoomFunction = RoomFunction.CUSTOM
    target_area: float = 0.0  # m²
    min_area: float = 0.0
    max_area: float = 0.0
    origin: Point2D = field(default_factory=Point2D)
    width: float = 0.0  # actual placed width
    depth: float = 0.0  # actual placed depth
    floor_finish: str = "Concrete"
    wall_finish: str = "Paint"
    ceiling_finish: str = "Gypsum"
    ceiling_height: float = 3.0

    @property
    def actual_area(self) -> float:
        return self.width * self.depth

    @property
    def bounds(self) -> BoundingBox:
        return BoundingBox(
            self.origin,
            Point2D(self.origin.x + self.width, self.origin.y + self.depth),
        )

    @property
    def is_habitable(self) -> bool:
        return self.function in {
            RoomFunction.BEDROOM, RoomFunction.LIVING, RoomFunction.KITCHEN,
            RoomFunction.DINING, RoomFunction.OFFICE,
        }


@dataclass
class Zone:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    room_ids: list[str] = field(default_factory=list)


@dataclass
class Level:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Level 1"
    elevation: float = 0.0  # meters above datum
    floor_to_floor: float = 3.0
    rooms: list[Room] = field(default_factory=list)
    walls: list[Wall] = field(default_factory=list)
    doors: list[Door] = field(default_factory=list)
    windows: list[Window] = field(default_factory=list)
    openings: list[Opening] = field(default_factory=list)
    zones: list[Zone] = field(default_factory=list)

    @property
    def bounds(self) -> Optional[BoundingBox]:
        if not self.rooms:
            return None
        min_x = min(r.origin.x for r in self.rooms)
        min_y = min(r.origin.y for r in self.rooms)
        max_x = max(r.origin.x + r.width for r in self.rooms)
        max_y = max(r.origin.y + r.depth for r in self.rooms)
        return BoundingBox(Point2D(min_x, min_y), Point2D(max_x, max_y))


@dataclass
class Building:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Building A"
    levels: list[Level] = field(default_factory=list)
    address: str = ""

    @property
    def total_area(self) -> float:
        return sum(r.actual_area for lvl in self.levels for r in lvl.rooms)


@dataclass
class Site:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Site"
    buildings: list[Building] = field(default_factory=list)
    boundary: list[Point2D] = field(default_factory=list)


@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Untitled Project"
    number: str = ""
    client: str = ""
    site: Site = field(default_factory=Site)
    revision: int = 1

    @property
    def building(self) -> Optional[Building]:
        if self.site.buildings:
            return self.site.buildings[0]
        return None
