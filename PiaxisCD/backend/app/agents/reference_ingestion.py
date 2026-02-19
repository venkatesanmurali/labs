"""Reference Ingestion Agent - handles image storage and scale calibration."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agents.base import BaseAgent


@dataclass
class ReferenceImage:
    filename: str = ""
    path: Path = Path(".")
    width_px: int = 0
    height_px: int = 0
    scale_factor: float | None = None  # pixels per meter


@dataclass
class IngestionResult:
    images: list[ReferenceImage]
    anchor_points: list[tuple[float, float]]


class ReferenceIngestionAgent(BaseAgent):
    """Stores reference images and manages calibration data."""

    def run(self, image_paths: list[Path], output_dir: Path) -> IngestionResult:
        self.log(f"Ingesting {len(image_paths)} reference images")
        output_dir.mkdir(parents=True, exist_ok=True)

        images = []
        for img_path in image_paths:
            if not img_path.exists():
                self.log(f"Skipping missing file: {img_path}")
                continue

            dest = output_dir / img_path.name
            shutil.copy2(img_path, dest)

            ref = ReferenceImage(
                filename=img_path.name,
                path=dest,
            )

            # Try to read image dimensions
            try:
                from PIL import Image
                with Image.open(dest) as im:
                    ref.width_px, ref.height_px = im.size
            except Exception:
                pass

            images.append(ref)

        self.log(f"Ingested {len(images)} images")
        return IngestionResult(images=images, anchor_points=[])

    def calibrate(self, ref: ReferenceImage, pixel_dist: float, real_dist: float) -> float:
        """Set scale factor from a known measurement."""
        scale = pixel_dist / real_dist
        ref.scale_factor = scale
        self.log(f"Calibrated {ref.filename}: {scale:.2f} px/m")
        return scale
