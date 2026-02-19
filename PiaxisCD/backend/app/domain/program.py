"""Program requirements and design constraints for CD generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domain.project import RoomFunction


@dataclass
class RoomRequirement:
    name: str = ""
    function: RoomFunction = RoomFunction.CUSTOM
    area: float = 0.0  # target area m²
    min_area: float = 0.0
    max_area: float = 0.0
    count: int = 1
    adjacencies: list[str] = field(default_factory=list)  # names of adjacent rooms
    must_have_window: Optional[bool] = None  # None = auto-detect from function
    floor_finish: str = "Concrete"
    wall_finish: str = "Paint"
    ceiling_finish: str = "Gypsum"
    ceiling_height: float = 3.0

    def __post_init__(self):
        if self.min_area == 0:
            self.min_area = self.area * 0.85
        if self.max_area == 0:
            self.max_area = self.area * 1.15


@dataclass
class DesignConstraints:
    max_footprint_width: float = 30.0  # meters
    max_footprint_depth: float = 20.0
    min_corridor_width: float = 1.2
    min_door_width: float = 0.9
    default_wall_thickness: float = 0.2
    exterior_wall_thickness: float = 0.3
    floor_to_floor_height: float = 3.0
    door_height: float = 2.1
    window_sill_height: float = 0.9
    window_height: float = 1.5
    min_window_area_ratio: float = 0.1  # 10% of floor area for habitable rooms
    building_code: str = "IBC"


@dataclass
class ProgramRequirements:
    project_name: str = "Untitled"
    project_number: str = ""
    client: str = ""
    rooms: list[RoomRequirement] = field(default_factory=list)
    constraints: DesignConstraints = field(default_factory=DesignConstraints)
    notes: str = ""

    @property
    def total_target_area(self) -> float:
        return sum(r.area * r.count for r in self.rooms)

    @property
    def expanded_rooms(self) -> list[RoomRequirement]:
        """Expand rooms with count > 1 into individual entries."""
        result = []
        for room in self.rooms:
            for i in range(room.count):
                r = RoomRequirement(
                    name=f"{room.name} {i + 1}" if room.count > 1 else room.name,
                    function=room.function,
                    area=room.area,
                    min_area=room.min_area,
                    max_area=room.max_area,
                    count=1,
                    adjacencies=room.adjacencies,
                    must_have_window=room.must_have_window,
                    floor_finish=room.floor_finish,
                    wall_finish=room.wall_finish,
                    ceiling_finish=room.ceiling_finish,
                    ceiling_height=room.ceiling_height,
                )
                result.append(r)
        return result
