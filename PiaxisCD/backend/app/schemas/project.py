"""Pydantic schemas for project API."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    number: str = ""
    client: str = ""
    description: str = ""


class ProjectUpdate(BaseModel):
    name: str | None = None
    number: str | None = None
    client: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    number: str
    client: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
