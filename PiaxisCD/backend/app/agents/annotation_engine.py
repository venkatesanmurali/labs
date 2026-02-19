"""CD Annotation Engine - adds dimensions, tags, room labels per layer."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.base import BaseAgent
from app.domain.annotations import Dimension, DimensionStyle, ElevationMarker, RoomTag, SectionMarker
from app.domain.geometry import Line2D, Point2D
from app.domain.project import Level


@dataclass
class AnnotationResult:
    dimensions: list[Dimension] = field(default_factory=list)
    room_tags: list[RoomTag] = field(default_factory=list)
    elevation_markers: list[ElevationMarker] = field(default_factory=list)
    section_markers: list[SectionMarker] = field(default_factory=list)


class CDAnnotationEngine(BaseAgent):
    """Adds dimensions, room tags, and markers to the plan."""

    def run(self, level: Level) -> AnnotationResult:
        self.log("Generating annotations")
        result = AnnotationResult()

        # Room tags at center of each room
        for i, room in enumerate(level.rooms):
            center = room.bounds.center
            result.room_tags.append(RoomTag(
                position=center,
                room_name=room.name,
                room_number=str(100 + i + 1),
                area=room.actual_area,
            ))

        # Overall dimensions along exterior
        if level.bounds:
            b = level.bounds
            offset = 1.5  # dimension line offset from building

            # Width dimension (bottom)
            result.dimensions.append(Dimension(
                start=Point2D(b.min_pt.x, b.min_pt.y - offset),
                end=Point2D(b.max_pt.x, b.min_pt.y - offset),
                offset=offset,
                value=b.width,
                style=DimensionStyle.LINEAR,
            ))

            # Depth dimension (left)
            result.dimensions.append(Dimension(
                start=Point2D(b.min_pt.x - offset, b.min_pt.y),
                end=Point2D(b.min_pt.x - offset, b.max_pt.y),
                offset=offset,
                value=b.height,
                style=DimensionStyle.LINEAR,
            ))

        # Room width/depth dimensions
        for room in level.rooms:
            rb = room.bounds
            dim_offset = 0.6

            # Width
            result.dimensions.append(Dimension(
                start=Point2D(rb.min_pt.x, rb.min_pt.y - dim_offset),
                end=Point2D(rb.max_pt.x, rb.min_pt.y - dim_offset),
                offset=dim_offset,
                value=room.width,
            ))

            # Depth
            result.dimensions.append(Dimension(
                start=Point2D(rb.min_pt.x - dim_offset, rb.min_pt.y),
                end=Point2D(rb.min_pt.x - dim_offset, rb.max_pt.y),
                offset=dim_offset,
                value=room.depth,
            ))

        # Elevation markers at building corners
        if level.bounds:
            b = level.bounds
            center = b.center
            markers = [
                ("N", Point2D(center.x, b.max_pt.y + 2)),
                ("S", Point2D(center.x, b.min_pt.y - 2)),
                ("E", Point2D(b.max_pt.x + 2, center.y)),
                ("W", Point2D(b.min_pt.x - 2, center.y)),
            ]
            for direction, pos in markers:
                result.elevation_markers.append(ElevationMarker(
                    position=pos,
                    direction=direction,
                ))

        # Section marker through building center
        if level.bounds:
            b = level.bounds
            center = b.center
            result.section_markers.append(SectionMarker(
                cut_line=Line2D(
                    Point2D(b.min_pt.x - 1, center.y),
                    Point2D(b.max_pt.x + 1, center.y),
                ),
                label="A",
            ))

        self.log(f"Generated {len(result.dimensions)} dims, {len(result.room_tags)} tags, "
                 f"{len(result.elevation_markers)} elev markers")

        return result
