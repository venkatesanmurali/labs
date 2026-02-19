"""Tests for design constraints and program requirements."""
from app.domain.program import DesignConstraints, ProgramRequirements, RoomRequirement
from app.domain.project import RoomFunction


def test_room_requirement_defaults():
    r = RoomRequirement(name="Test", area=20)
    assert r.min_area == 17.0  # 85% of 20
    assert r.max_area == 23.0  # 115% of 20


def test_design_constraints_defaults():
    c = DesignConstraints()
    assert c.min_corridor_width == 1.2
    assert c.min_door_width == 0.9
    assert c.floor_to_floor_height == 3.0


def test_total_target_area():
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name="A", area=20, count=2),
        RoomRequirement(name="B", area=10, count=1),
    ])
    assert reqs.total_target_area == 50  # 20*2 + 10*1


def test_expanded_rooms_count():
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name="Bedroom", area=15, count=3),
        RoomRequirement(name="Bath", area=5, count=1),
    ])
    expanded = reqs.expanded_rooms
    assert len(expanded) == 4
    bedrooms = [r for r in expanded if "Bedroom" in r.name]
    assert len(bedrooms) == 3


def test_habitable_room_detection():
    from app.domain.project import Room
    living = Room(name="Living", function=RoomFunction.LIVING, width=5, depth=5)
    assert living.is_habitable
    storage = Room(name="Storage", function=RoomFunction.STORAGE, width=3, depth=3)
    assert not storage.is_habitable
