"""Export package and manifest models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ExportFormat(Enum):
    DXF = "dxf"
    IFC = "ifc"
    PDF = "pdf"
    PNG = "png"


@dataclass
class ExportFile:
    filename: str = ""
    format: ExportFormat = ExportFormat.DXF
    path: Path = field(default_factory=lambda: Path("."))
    size_bytes: int = 0
    sheet_number: str = ""
    description: str = ""


@dataclass
class ExportManifest:
    project_name: str = ""
    project_number: str = ""
    revision: int = 1
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generator: str = "PiaxisCD v0.1.0"
    files: list[ExportFile] = field(default_factory=list)
    total_sheets: int = 0
    formats: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "project_number": self.project_number,
            "revision": self.revision,
            "generated_at": self.generated_at,
            "generator": self.generator,
            "total_sheets": self.total_sheets,
            "formats": self.formats,
            "files": [
                {
                    "filename": f.filename,
                    "format": f.format.value,
                    "size_bytes": f.size_bytes,
                    "sheet_number": f.sheet_number,
                    "description": f.description,
                }
                for f in self.files
            ],
        }


@dataclass
class ExportPackage:
    manifest: ExportManifest = field(default_factory=ExportManifest)
    output_dir: Path = field(default_factory=lambda: Path("."))
    zip_path: Path | None = None

    def add_file(self, ef: ExportFile) -> None:
        self.manifest.files.append(ef)

    @property
    def file_count(self) -> int:
        return len(self.manifest.files)
