"""Requirements Interpreter Agent - parses text/JSON into ProgramRequirements."""
from __future__ import annotations

import json
import re
from typing import Any

from app.agents.base import BaseAgent
from app.domain.program import (
    DesignConstraints,
    ProgramRequirements,
    RoomRequirement,
)
from app.domain.project import RoomFunction

FUNCTION_MAP = {
    "bedroom": RoomFunction.BEDROOM,
    "living": RoomFunction.LIVING,
    "living room": RoomFunction.LIVING,
    "kitchen": RoomFunction.KITCHEN,
    "bathroom": RoomFunction.BATHROOM,
    "bath": RoomFunction.BATHROOM,
    "dining": RoomFunction.DINING,
    "dining room": RoomFunction.DINING,
    "office": RoomFunction.OFFICE,
    "study": RoomFunction.OFFICE,
    "storage": RoomFunction.STORAGE,
    "corridor": RoomFunction.CORRIDOR,
    "hallway": RoomFunction.CORRIDOR,
    "lobby": RoomFunction.LOBBY,
    "entry": RoomFunction.LOBBY,
    "utility": RoomFunction.UTILITY,
    "laundry": RoomFunction.UTILITY,
    "mechanical": RoomFunction.MECHANICAL,
    "garage": RoomFunction.GARAGE,
}


class RequirementsInterpreterAgent(BaseAgent):
    """Parses text or JSON requirements into structured ProgramRequirements."""

    def run(self, input_data: str | dict) -> ProgramRequirements:
        if isinstance(input_data, dict):
            return self._parse_json(input_data)
        # Try JSON string first
        try:
            data = json.loads(input_data)
            return self._parse_json(data)
        except (json.JSONDecodeError, TypeError):
            return self._parse_text(input_data)

    def _parse_json(self, data: dict) -> ProgramRequirements:
        self.log("Parsing JSON requirements")
        rooms = []
        for r in data.get("rooms", []):
            func_str = r.get("function", "custom").lower()
            rooms.append(RoomRequirement(
                name=r.get("name", "Room"),
                function=FUNCTION_MAP.get(func_str, RoomFunction.CUSTOM),
                area=float(r.get("area", 15)),
                count=int(r.get("count", 1)),
                adjacencies=r.get("adjacencies", []),
                must_have_window=r.get("must_have_window"),
                floor_finish=r.get("floor_finish", "Concrete"),
                wall_finish=r.get("wall_finish", "Paint"),
                ceiling_finish=r.get("ceiling_finish", "Gypsum"),
                ceiling_height=float(r.get("ceiling_height", 3.0)),
            ))

        constraints = DesignConstraints()
        if "constraints" in data:
            c = data["constraints"]
            for key in vars(constraints):
                if key in c:
                    setattr(constraints, key, c[key])

        return ProgramRequirements(
            project_name=data.get("project_name", "Untitled"),
            project_number=data.get("project_number", ""),
            client=data.get("client", ""),
            rooms=rooms,
            constraints=constraints,
            notes=data.get("notes", ""),
        )

    def _parse_text(self, text: str) -> ProgramRequirements:
        self.log("Parsing text requirements")
        rooms = []
        lines = text.strip().split("\n")

        project_name = "Untitled"
        notes_lines = []

        # Pattern: "2 bedrooms, 15 sqm each" or "Living Room: 25 sqm" or "1x Kitchen (12 m²)"
        room_pattern = re.compile(
            r"(?:(\d+)\s*x?\s+)?"  # optional count
            r"([\w\s]+?)"           # room name
            r"[\s:,\-]+?"
            r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|m²|sqm|square\s*met)",  # area
            re.IGNORECASE,
        )

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                if line.startswith("# "):
                    project_name = line[2:].strip()
                continue

            match = room_pattern.search(line)
            if match:
                count = int(match.group(1) or 1)
                name = match.group(2).strip().title()
                area = float(match.group(3))
                func = FUNCTION_MAP.get(name.lower(), RoomFunction.CUSTOM)

                rooms.append(RoomRequirement(
                    name=name,
                    function=func,
                    area=area,
                    count=count,
                ))
            else:
                notes_lines.append(line)

        if not rooms:
            # Fallback: create a default room
            rooms.append(RoomRequirement(name="Room", area=20.0))

        return ProgramRequirements(
            project_name=project_name,
            rooms=rooms,
            notes="\n".join(notes_lines),
        )
