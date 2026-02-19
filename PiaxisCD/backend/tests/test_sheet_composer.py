"""Tests for SheetComposer."""
from app.agents.annotation_engine import AnnotationResult, CDAnnotationEngine
from app.agents.sheet_composer import SheetComposer
from app.agents.view_generator import ViewGenerator
from app.domain.geometry import Point2D
from app.domain.project import Level, Project, Building, Site, Room, RoomFunction


def _make_project():
    rooms = [
        Room(name="Living", function=RoomFunction.LIVING, origin=Point2D(0, 0), width=5, depth=5),
        Room(name="Bedroom", function=RoomFunction.BEDROOM, origin=Point2D(5.2, 0), width=4, depth=4),
    ]
    level = Level(rooms=rooms)
    building = Building(name="Test", levels=[level])
    site = Site(buildings=[building])
    return Project(name="Test Project", site=site), level


def test_sheets_created():
    project, level = _make_project()
    annotations = CDAnnotationEngine().run(level)
    views = ViewGenerator().run(level)
    composed = SheetComposer().run(project, views, annotations)

    sheet_set = composed.sheet_set
    assert len(sheet_set.sheets) >= 3  # floor plan + RCP + elevations


def test_floor_plan_sheet():
    project, level = _make_project()
    annotations = CDAnnotationEngine().run(level)
    views = ViewGenerator().run(level)
    composed = SheetComposer().run(project, views, annotations)

    fp_sheet = composed.sheet_set.get_sheet("A1.01")
    assert fp_sheet is not None
    assert fp_sheet.name == "Floor Plan"
    assert len(fp_sheet.viewports) == 1


def test_title_block():
    project, level = _make_project()
    annotations = CDAnnotationEngine().run(level)
    views = ViewGenerator().run(level)
    composed = SheetComposer().run(project, views, annotations)

    sheet = composed.sheet_set.sheets[0]
    assert sheet.title_block.project_name == "Test Project"
    assert sheet.title_block.sheet_number == "A1.01"
