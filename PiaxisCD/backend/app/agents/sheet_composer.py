"""Sheet Composer - composes sheets with viewports, title blocks, scale bars."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.agents.base import BaseAgent
from app.domain.annotations import NorthArrow, ScaleBar
from app.domain.geometry import Point2D
from app.domain.project import Project
from app.domain.sheets import (
    PAPER_SIZES_MM,
    PaperSize,
    Sheet,
    SheetSet,
    TitleBlock,
    Viewport,
)
from app.domain.views import ViewScale
from app.agents.annotation_engine import AnnotationResult
from app.agents.view_generator import ViewSet


@dataclass
class ComposedSheetSet:
    sheet_set: SheetSet
    north_arrows: dict[str, NorthArrow] = field(default_factory=dict)  # sheet_id -> arrow
    scale_bars: dict[str, ScaleBar] = field(default_factory=dict)


class SheetComposer(BaseAgent):
    """Composes sheets with viewports and title blocks."""

    def run(
        self,
        project: Project,
        view_set: ViewSet,
        annotations: AnnotationResult,
        paper_size: PaperSize = PaperSize.ARCH_D,
        scale: ViewScale | None = None,
    ) -> ComposedSheetSet:
        self.log("Composing sheets")
        if scale is None:
            scale = ViewScale(1, 100)

        sheet_set = SheetSet(name=f"{project.name} - CD Set")
        composed = ComposedSheetSet(sheet_set=sheet_set)

        paper_w, paper_h = PAPER_SIZES_MM[paper_size]
        # paper_h is the short dimension, paper_w is long (landscape)
        # Swap for landscape
        if paper_h > paper_w:
            paper_w, paper_h = paper_h, paper_w

        margin = 15.0
        title_block_h = 60.0
        drawable_w = paper_w - 2 * margin
        drawable_h = paper_h - 2 * margin - title_block_h

        # Sheet A1.01 - Floor Plan
        if view_set.floor_plan:
            sheet = self._create_sheet(
                "A1.01", "Floor Plan", project, paper_size, scale
            )
            vp = Viewport(
                view_id=view_set.floor_plan.id,
                view_name=view_set.floor_plan.name,
                position=Point2D(margin + 10, margin + title_block_h + 10),
                width=min(drawable_w - 20, 600),
                height=min(drawable_h - 20, 400),
                scale=scale,
                view_data=view_set.floor_plan,
            )
            sheet.viewports.append(vp)
            sheet_set.add_sheet(sheet)

            # Add north arrow and scale bar
            composed.north_arrows[sheet.id] = NorthArrow(
                position=Point2D(paper_w - margin - 30, paper_h - margin - 30),
                size=15.0,
            )
            composed.scale_bars[sheet.id] = ScaleBar(
                position=Point2D(margin + 20, margin + title_block_h + 5),
                scale_text=str(scale),
            )

        # Sheet A1.02 - RCP
        if view_set.rcp:
            sheet = self._create_sheet(
                "A1.02", "Reflected Ceiling Plan", project, paper_size, scale
            )
            vp = Viewport(
                view_id=view_set.rcp.id,
                view_name=view_set.rcp.name,
                position=Point2D(margin + 10, margin + title_block_h + 10),
                width=min(drawable_w - 20, 600),
                height=min(drawable_h - 20, 400),
                scale=scale,
                view_data=view_set.rcp,
            )
            sheet.viewports.append(vp)
            sheet_set.add_sheet(sheet)

        # Sheet A2.01 - Elevations (2 per sheet)
        elevations = view_set.elevations
        for i in range(0, len(elevations), 2):
            batch = elevations[i:i + 2]
            sheet_num = f"A2.{(i // 2) + 1:02d}"
            names = " / ".join(e.name for e in batch)
            sheet = self._create_sheet(
                sheet_num, f"Elevations - {names}", project, paper_size, scale
            )

            for j, elev in enumerate(batch):
                vp_y = margin + title_block_h + 10 + j * (drawable_h / 2)
                vp = Viewport(
                    view_id=elev.id,
                    view_name=elev.name,
                    position=Point2D(margin + 10, vp_y),
                    width=min(drawable_w - 20, 600),
                    height=min(drawable_h / 2 - 20, 200),
                    scale=scale,
                    view_data=elev,
                )
                sheet.viewports.append(vp)

            sheet_set.add_sheet(sheet)

        # Sheet A3.01 - Sections
        for i, section in enumerate(view_set.sections):
            sheet = self._create_sheet(
                f"A3.{i + 1:02d}", f"Section {section.name}", project, paper_size,
                section.scale,
            )
            vp = Viewport(
                view_id=section.id,
                view_name=section.name,
                position=Point2D(margin + 10, margin + title_block_h + 10),
                width=min(drawable_w - 20, 600),
                height=min(drawable_h - 20, 300),
                scale=section.scale,
                view_data=section,
            )
            sheet.viewports.append(vp)
            sheet_set.add_sheet(sheet)

        self.log(f"Composed {len(sheet_set.sheets)} sheets")
        return composed

    def _create_sheet(
        self,
        number: str,
        name: str,
        project: Project,
        paper_size: PaperSize,
        scale: ViewScale,
    ) -> Sheet:
        tb = TitleBlock(
            project_name=project.name,
            project_number=project.number,
            sheet_name=name,
            sheet_number=number,
            date=date.today().isoformat(),
            revision=str(project.revision),
            scale=str(scale),
        )
        return Sheet(
            number=number,
            name=name,
            paper_size=paper_size,
            title_block=tb,
        )
