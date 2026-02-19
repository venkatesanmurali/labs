"""Tests for SchematicPlanGenerator."""
from app.agents.schematic_plan import SchematicPlanGenerator
from app.domain.program import ProgramRequirements, RoomRequirement
from app.domain.project import RoomFunction


def test_basic_plan_generation():
    agent = SchematicPlanGenerator()
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name="Living", function=RoomFunction.LIVING, area=25),
        RoomRequirement(name="Bedroom", function=RoomFunction.BEDROOM, area=16),
        RoomRequirement(name="Bath", function=RoomFunction.BATHROOM, area=6),
    ])
    result = agent.run(reqs)
    project = result.project
    assert project.building is not None
    level = project.building.levels[0]
    assert len(level.rooms) == 3
    assert len(level.walls) > 0
    assert len(level.doors) > 0


def test_rooms_dont_overlap():
    agent = SchematicPlanGenerator()
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name=f"Room {i}", area=15) for i in range(5)
    ])
    result = agent.run(reqs)
    level = result.project.building.levels[0]

    # Check no overlapping room bounds
    for i, a in enumerate(level.rooms):
        for b in level.rooms[i + 1:]:
            ab, bb = a.bounds, b.bounds
            overlap = not (ab.max_pt.x <= bb.min_pt.x or
                          bb.max_pt.x <= ab.min_pt.x or
                          ab.max_pt.y <= bb.min_pt.y or
                          bb.max_pt.y <= ab.min_pt.y)
            assert not overlap, f"{a.name} overlaps {b.name}"


def test_habitable_rooms_get_windows():
    agent = SchematicPlanGenerator()
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name="Living", function=RoomFunction.LIVING, area=25),
        RoomRequirement(name="Bedroom", function=RoomFunction.BEDROOM, area=16),
    ])
    result = agent.run(reqs)
    level = result.project.building.levels[0]
    assert len(level.windows) >= 1  # At least some windows placed


def test_exterior_walls_created():
    agent = SchematicPlanGenerator()
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name="Room", area=20),
    ])
    result = agent.run(reqs)
    level = result.project.building.levels[0]
    from app.domain.geometry import WallType
    ext_walls = [w for w in level.walls if w.wall_type == WallType.EXTERIOR]
    assert len(ext_walls) == 4  # 4 exterior walls for single room


def test_deterministic_with_seed():
    reqs = ProgramRequirements(rooms=[
        RoomRequirement(name="A", area=20),
        RoomRequirement(name="B", area=15),
    ])
    from app.agents.base import AgentContext
    r1 = SchematicPlanGenerator(AgentContext(seed=42)).run(reqs)
    r2 = SchematicPlanGenerator(AgentContext(seed=42)).run(reqs)
    # Same seed should produce same room dimensions
    for a, b in zip(r1.project.building.levels[0].rooms, r2.project.building.levels[0].rooms):
        assert a.width == b.width
        assert a.depth == b.depth
