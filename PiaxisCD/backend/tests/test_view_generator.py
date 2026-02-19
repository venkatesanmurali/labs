"""Tests for ViewGenerator."""
from app.agents.view_generator import ViewGenerator
from app.domain.geometry import Point2D
from app.domain.project import Level, Room, RoomFunction
from app.domain.views import ElevationDirection


def test_generates_all_view_types():
    level = Level(rooms=[
        Room(name="Room", origin=Point2D(0, 0), width=5, depth=5),
    ])
    gen = ViewGenerator()
    view_set = gen.run(level)

    assert view_set.floor_plan is not None
    assert view_set.rcp is not None
    assert len(view_set.elevations) == 4
    assert len(view_set.sections) >= 1


def test_elevation_directions():
    level = Level(rooms=[Room(origin=Point2D(0, 0), width=5, depth=5)])
    gen = ViewGenerator()
    view_set = gen.run(level)

    directions = {e.direction for e in view_set.elevations}
    assert directions == {
        ElevationDirection.NORTH,
        ElevationDirection.SOUTH,
        ElevationDirection.EAST,
        ElevationDirection.WEST,
    }


def test_empty_level():
    gen = ViewGenerator()
    view_set = gen.run(Level())
    assert view_set.floor_plan is None
