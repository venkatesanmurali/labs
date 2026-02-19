"""Sheet set and composition models for CD output."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from app.domain.geometry import BoundingBox, Point2D
from app.domain.views import ViewScale


class PaperSize(Enum):
    ARCH_D = "ARCH_D"  # 24" x 36"  (610 x 914 mm)
    ARCH_E = "ARCH_E"  # 36" x 48"
    A1 = "A1"          # 594 x 841 mm
    A2 = "A2"          # 420 x 594 mm
    A3 = "A3"          # 297 x 420 mm


PAPER_SIZES_MM = {
    PaperSize.ARCH_D: (610.0, 914.0),
    PaperSize.ARCH_E: (914.0, 1219.0),
    PaperSize.A1: (594.0, 841.0),
    PaperSize.A2: (420.0, 594.0),
    PaperSize.A3: (297.0, 420.0),
}


@dataclass
class TitleBlock:
    project_name: str = ""
    project_number: str = ""
    sheet_name: str = ""
    sheet_number: str = ""
    drawn_by: str = "PiaxisCD"
    checked_by: str = ""
    date: str = ""
    revision: str = "0"
    scale: str = "As Noted"
    firm_name: str = "Piaxis"
    position: Point2D = field(default_factory=Point2D)
    width: float = 180.0  # mm
    height: float = 60.0  # mm


@dataclass
class Viewport:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    view_id: str = ""
    view_name: str = ""
    position: Point2D = field(default_factory=Point2D)  # on sheet, mm
    width: float = 400.0  # mm on sheet
    height: float = 300.0
    scale: ViewScale = field(default_factory=lambda: ViewScale(1, 100))
    view_data: Any = None  # reference to actual view object


@dataclass
class Sheet:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    number: str = "A1.01"
    name: str = "Floor Plan"
    paper_size: PaperSize = PaperSize.ARCH_D
    viewports: list[Viewport] = field(default_factory=list)
    title_block: TitleBlock = field(default_factory=TitleBlock)
    margin: float = 15.0  # mm

    @property
    def paper_width_mm(self) -> float:
        return PAPER_SIZES_MM[self.paper_size][1]

    @property
    def paper_height_mm(self) -> float:
        return PAPER_SIZES_MM[self.paper_size][0]

    @property
    def drawable_bounds(self) -> BoundingBox:
        return BoundingBox(
            Point2D(self.margin, self.margin),
            Point2D(self.paper_width_mm - self.margin,
                     self.paper_height_mm - self.margin),
        )


@dataclass
class SheetSet:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "CD Set"
    sheets: list[Sheet] = field(default_factory=list)

    def add_sheet(self, sheet: Sheet) -> None:
        self.sheets.append(sheet)

    def get_sheet(self, number: str) -> Optional[Sheet]:
        return next((s for s in self.sheets if s.number == number), None)
