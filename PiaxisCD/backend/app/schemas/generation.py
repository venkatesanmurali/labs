"""Pydantic schemas for generation jobs."""
from __future__ import annotations

from pydantic import BaseModel


class GenerationConfig(BaseModel):
    formats: list[str] = ["dxf", "pdf", "png"]
    paper_size: str = "ARCH_D"
    scale: str = "1:100"
    seed: int = 42
    include_schedules: bool = True
    include_qc: bool = True


class GenerationRequest(BaseModel):
    config: GenerationConfig = GenerationConfig()


class GenerationStatus(BaseModel):
    revision_id: str
    status: str
    progress: float = 0.0
    message: str = ""
    artifacts_count: int = 0
    qc_issues_count: int = 0
