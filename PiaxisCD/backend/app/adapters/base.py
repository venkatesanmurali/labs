"""Abstract adapter interface for CAD/BIM backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.export import ExportPackage
from app.domain.project import Project
from app.domain.views import ViewType


class CadBimAdapter(ABC):
    """Interface for CAD/BIM backend adapters."""

    @abstractmethod
    def create_project(self, project: Project) -> str:
        """Create a project in the CAD/BIM system. Returns project ID."""
        ...

    @abstractmethod
    def push_floorplan(self, project: Project) -> None:
        """Push floor plan model to the CAD/BIM system."""
        ...

    @abstractmethod
    def generate_views(self, project: Project, view_types: list[ViewType]) -> list[Any]:
        """Generate views from the model."""
        ...

    @abstractmethod
    def export(self, project: Project, formats: list[str]) -> ExportPackage:
        """Export to specified formats."""
        ...
