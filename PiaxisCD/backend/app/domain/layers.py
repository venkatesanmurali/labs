"""CAD layer definitions following AIA layering conventions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LayerColor(Enum):
    WHITE = 7
    RED = 1
    YELLOW = 2
    GREEN = 3
    CYAN = 4
    BLUE = 5
    MAGENTA = 6
    GRAY = 8


@dataclass(frozen=True)
class CadLayer:
    name: str
    color: int
    linetype: str = "Continuous"
    lineweight: float = 0.25  # mm
    description: str = ""


# Standard AEC layers
LAYERS = {
    "A-WALL": CadLayer("A-WALL", LayerColor.WHITE.value, lineweight=0.50, description="Walls"),
    "A-WALL-EXTR": CadLayer("A-WALL-EXTR", LayerColor.WHITE.value, lineweight=0.70, description="Exterior walls"),
    "A-DOOR": CadLayer("A-DOOR", LayerColor.RED.value, lineweight=0.35, description="Doors"),
    "A-DOOR-SWING": CadLayer("A-DOOR-SWING", LayerColor.RED.value, "DASHED", 0.18, "Door swings"),
    "A-WIND": CadLayer("A-WIND", LayerColor.CYAN.value, lineweight=0.35, description="Windows"),
    "A-GLAZ": CadLayer("A-GLAZ", LayerColor.CYAN.value, lineweight=0.25, description="Glazing"),
    "A-COLS": CadLayer("A-COLS", LayerColor.GREEN.value, lineweight=0.50, description="Columns"),
    "A-ROOM-NAME": CadLayer("A-ROOM-NAME", LayerColor.BLUE.value, lineweight=0.18, description="Room names"),
    "A-ROOM-AREA": CadLayer("A-ROOM-AREA", LayerColor.BLUE.value, lineweight=0.18, description="Room areas"),
    "A-ROOM-NUMB": CadLayer("A-ROOM-NUMB", LayerColor.BLUE.value, lineweight=0.18, description="Room numbers"),
    "A-DIMS": CadLayer("A-DIMS", LayerColor.YELLOW.value, lineweight=0.18, description="Dimensions"),
    "A-ANNO": CadLayer("A-ANNO", LayerColor.GREEN.value, lineweight=0.18, description="Annotations"),
    "A-ANNO-TAG": CadLayer("A-ANNO-TAG", LayerColor.GREEN.value, lineweight=0.25, description="Tags"),
    "A-ELEV-IDEN": CadLayer("A-ELEV-IDEN", LayerColor.MAGENTA.value, lineweight=0.25, description="Elevation markers"),
    "A-SECT-IDEN": CadLayer("A-SECT-IDEN", LayerColor.MAGENTA.value, lineweight=0.25, description="Section markers"),
    "A-FLOR-PATT": CadLayer("A-FLOR-PATT", LayerColor.GRAY.value, lineweight=0.13, description="Floor patterns"),
    "A-CEIL-GRID": CadLayer("A-CEIL-GRID", LayerColor.GRAY.value, "DASHED", 0.13, "Ceiling grid"),
    "G-ANNO-TTLB": CadLayer("G-ANNO-TTLB", LayerColor.WHITE.value, lineweight=0.50, description="Title block"),
    "G-ANNO-NOTE": CadLayer("G-ANNO-NOTE", LayerColor.WHITE.value, lineweight=0.18, description="General notes"),
}


def get_layer(name: str) -> CadLayer:
    return LAYERS.get(name, CadLayer(name, LayerColor.WHITE.value))
