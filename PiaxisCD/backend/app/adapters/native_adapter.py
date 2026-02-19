"""Native adapter using built-in ezdxf/ifcopenshell/reportlab."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.adapters.base import CadBimAdapter
from app.agents.annotation_engine import CDAnnotationEngine
from app.agents.base import AgentContext
from app.agents.export_agent import ExportAgent
from app.agents.sheet_composer import SheetComposer
from app.agents.view_generator import ViewGenerator
from app.domain.export import ExportPackage
from app.domain.project import Project
from app.domain.views import ViewType


class NativeAdapter(CadBimAdapter):
    """Built-in adapter using Python libraries for export."""

    def __init__(self, output_dir: Path, context: AgentContext | None = None):
        self.output_dir = output_dir
        self.context = context or AgentContext()

    def create_project(self, project: Project) -> str:
        return project.id

    def push_floorplan(self, project: Project) -> None:
        pass  # No external system to push to

    def generate_views(self, project: Project, view_types: list[ViewType]) -> list[Any]:
        level = project.building.levels[0] if project.building else None
        if not level:
            return []
        gen = ViewGenerator(self.context)
        return [gen.run(level)]

    def export(self, project: Project, formats: list[str]) -> ExportPackage:
        level = project.building.levels[0] if project.building else None
        if not level:
            return ExportPackage()

        annotator = CDAnnotationEngine(self.context)
        annotations = annotator.run(level)

        view_gen = ViewGenerator(self.context)
        view_set = view_gen.run(level)

        composer = SheetComposer(self.context)
        composed = composer.run(project, view_set, annotations)

        exporter = ExportAgent(self.context)
        return exporter.run(project, level, annotations, composed, self.output_dir, formats)
