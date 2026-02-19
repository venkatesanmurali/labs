"""Project CRUD routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    svc = ProjectService(db)
    project = await svc.create_project(data)
    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    svc = ProjectService(db)
    projects, total = await svc.list_projects(skip, limit)
    return ProjectListResponse(projects=projects, total=total)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    svc = ProjectService(db)
    project = await svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    svc = ProjectService(db)
    project = await svc.update_project(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    svc = ProjectService(db)
    deleted = await svc.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
