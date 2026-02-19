"""Tests for CDAnnotationEngine."""
from app.agents.annotation_engine import CDAnnotationEngine
from app.domain.geometry import Point2D
from app.domain.project import Level, Room, RoomFunction


def _make_level():
    rooms = [
        Room(name="Living", function=RoomFunction.LIVING, origin=Point2D(0, 0), width=5, depth=5),
        Room(name="Bedroom", function=RoomFunction.BEDROOM, origin=Point2D(5.2, 0), width=4, depth=4),
    ]
    return Level(rooms=rooms)


def test_room_tags_generated():
    engine = CDAnnotationEngine()
    result = engine.run(_make_level())
    assert len(result.room_tags) == 2
    assert result.room_tags[0].room_name == "Living"
    assert result.room_tags[0].area == 25.0  # 5*5


def test_dimensions_generated():
    engine = CDAnnotationEngine()
    result = engine.run(_make_level())
    # Should have overall + per-room dims
    assert len(result.dimensions) >= 4


def test_elevation_markers():
    engine = CDAnnotationEngine()
    result = engine.run(_make_level())
    assert len(result.elevation_markers) == 4  # N, S, E, W


def test_section_markers():
    engine = CDAnnotationEngine()
    result = engine.run(_make_level())
    assert len(result.section_markers) >= 1
