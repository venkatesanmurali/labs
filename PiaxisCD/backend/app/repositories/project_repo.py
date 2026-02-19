"""Repository for project CRUD operations."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectModel


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> ProjectModel:
        project = ProjectModel(**kwargs)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get(self, project_id: str) -> ProjectModel | None:
        return await self.db.get(ProjectModel, project_id)

    async def list_all(self, skip: int = 0, limit: int = 50) -> list[ProjectModel]:
        result = await self.db.execute(
            select(ProjectModel).order_by(ProjectModel.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(ProjectModel))
        return len(result.scalars().all())

    async def update(self, project_id: str, **kwargs) -> ProjectModel | None:
        project = await self.get(project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: str) -> bool:
        project = await self.get(project_id)
        if not project:
            return False
        await self.db.delete(project)
        await self.db.commit()
        return True
