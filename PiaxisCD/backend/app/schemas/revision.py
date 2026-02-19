"""Pydantic schemas for revisions."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class RevisionResponse(BaseModel):
    id: str
    project_id: str
    revision_number: int
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
