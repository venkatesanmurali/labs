"""Stub adapter for future Revit/APS integration."""
from __future__ import annotations

from typing import Any

from app.adapters.base import CadBimAdapter
from app.domain.export import ExportPackage
from app.domain.project import Project
from app.domain.views import ViewType


class RevitAdapter(CadBimAdapter):
    """Stub for future Revit/APS integration.

    To implement:
    1. Connect to Revit via pyrevit or APS Design Automation API
    2. Push model elements as Revit families
    3. Use Revit's built-in view generation
    4. Export using Revit's export capabilities
    """

    def create_project(self, project: Project) -> str:
        raise NotImplementedError("Revit adapter not yet implemented")

    def push_floorplan(self, project: Project) -> None:
        raise NotImplementedError("Revit adapter not yet implemented")

    def generate_views(self, project: Project, view_types: list[ViewType]) -> list[Any]:
        raise NotImplementedError("Revit adapter not yet implemented")

    def export(self, project: Project, formats: list[str]) -> ExportPackage:
        raise NotImplementedError("Revit adapter not yet implemented")
