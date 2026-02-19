"""Pydantic schemas for export/artifact responses."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ArtifactResponse(BaseModel):
    id: str
    revision_id: str
    artifact_type: str
    filename: str
    file_path: str
    file_size: int
    sheet_number: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QCIssueResponse(BaseModel):
    id: str
    severity: str
    category: str
    message: str
    element_id: str

    model_config = {"from_attributes": True}


class ExportManifestResponse(BaseModel):
    project_name: str
    revision: int
    total_sheets: int
    formats: list[str]
    artifacts: list[ArtifactResponse]
    qc_issues: list[QCIssueResponse]
