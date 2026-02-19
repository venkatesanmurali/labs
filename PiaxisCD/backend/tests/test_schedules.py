"""Tests for schedule models."""
from app.domain.schedules import (
    DoorSchedule,
    DoorScheduleEntry,
    RoomFinishEntry,
    RoomFinishSchedule,
    WindowSchedule,
    WindowScheduleEntry,
)


def test_door_schedule():
    schedule = DoorSchedule(entries=[
        DoorScheduleEntry(mark="D01", width=0.9, height=2.1, door_type="Single"),
        DoorScheduleEntry(mark="D02", width=1.2, height=2.1, door_type="Double"),
    ])
    assert len(schedule.entries) == 2
    assert schedule.entries[0].mark == "D01"


def test_window_schedule():
    schedule = WindowSchedule(entries=[
        WindowScheduleEntry(mark="W01", width=1.2, height=1.5, sill_height=0.9),
    ])
    assert len(schedule.entries) == 1


def test_room_finish_schedule():
    schedule = RoomFinishSchedule(entries=[
        RoomFinishEntry(number="101", name="Living Room", area=25.0, floor_finish="Tile"),
    ])
    assert schedule.entries[0].name == "Living Room"
    assert schedule.entries[0].floor_finish == "Tile"
