"""Schedule models for CD output (door, window, room finish schedules)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DoorScheduleEntry:
    mark: str = ""
    room_from: str = ""
    room_to: str = ""
    width: float = 0.9
    height: float = 2.1
    door_type: str = "Single"
    material: str = "Wood"
    hardware: str = "Lever"
    fire_rating: str = ""
    notes: str = ""


@dataclass
class WindowScheduleEntry:
    mark: str = ""
    room: str = ""
    width: float = 1.2
    height: float = 1.5
    sill_height: float = 0.9
    window_type: str = "Fixed"
    material: str = "Aluminum"
    glazing: str = "Double"
    notes: str = ""


@dataclass
class RoomFinishEntry:
    number: str = ""
    name: str = ""
    area: float = 0.0
    floor_finish: str = ""
    wall_finish: str = ""
    ceiling_finish: str = ""
    ceiling_height: float = 3.0
    notes: str = ""


@dataclass
class DoorSchedule:
    entries: list[DoorScheduleEntry] = field(default_factory=list)
    title: str = "Door Schedule"


@dataclass
class WindowSchedule:
    entries: list[WindowScheduleEntry] = field(default_factory=list)
    title: str = "Window Schedule"


@dataclass
class RoomFinishSchedule:
    entries: list[RoomFinishEntry] = field(default_factory=list)
    title: str = "Room Finish Schedule"
