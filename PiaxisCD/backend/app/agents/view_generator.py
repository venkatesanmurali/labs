"""View Generator - derives elevations, sections, RCP from plan model."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.base import BaseAgent
from app.domain.geometry import Line2D, Point2D
from app.domain.project import Level
from app.domain.views import (
    ElevationDirection,
    ElevationView,
    FloorPlanView,
    RCPView,
    SectionView,
    ViewScale,
)


@dataclass
class ViewSet:
    floor_plan: FloorPlanView | None = None
    rcp: RCPView | None = None
    elevations: list[ElevationView] = field(default_factory=list)
    sections: list[SectionView] = field(default_factory=list)


class ViewGenerator(BaseAgent):
    """Generates views from the building model."""

    def run(self, level: Level, scale: ViewScale | None = None) -> ViewSet:
        self.log("Generating views")
        if scale is None:
            scale = ViewScale(1, 100)

        bounds = level.bounds
        if not bounds:
            return ViewSet()

        view_set = ViewSet()

        # Floor plan
        view_set.floor_plan = FloorPlanView(
            name=f"{level.name} - Floor Plan",
            level_id=level.id,
            cut_height=1.2,
            scale=scale,
            bounds=bounds,
        )

        # RCP
        view_set.rcp = RCPView(
            name=f"{level.name} - RCP",
            level_id=level.id,
            scale=scale,
            bounds=bounds,
        )

        # Elevations - 4 cardinal directions
        bw = bounds.width
        bh = bounds.height
        fh = level.floor_to_floor

        for direction in ElevationDirection:
            if direction in (ElevationDirection.NORTH, ElevationDirection.SOUTH):
                width = bw
            else:
                width = bh

            view_set.elevations.append(ElevationView(
                name=f"{direction.value.title()} Elevation",
                direction=direction,
                level_id=level.id,
                scale=scale,
                height=fh + 0.5,
                width=width + 1.0,
            ))

        # Section through center
        center = bounds.center
        view_set.sections.append(SectionView(
            name="Section A-A",
            cut_line=Line2D(
                Point2D(bounds.min_pt.x - 1, center.y),
                Point2D(bounds.max_pt.x + 1, center.y),
            ),
            level_id=level.id,
            scale=ViewScale(1, 50),
            height=fh + 0.5,
            width=bw + 2.0,
        ))

        self.log(f"Generated {1 + 1 + len(view_set.elevations) + len(view_set.sections)} views")

        return view_set
