"""Project service - business logic for projects."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectModel
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def create_project(self, data: ProjectCreate) -> ProjectModel:
        return await self.repo.create(
            name=data.name,
            number=data.number,
            client=data.client,
            description=data.description,
        )

    async def get_project(self, project_id: str) -> ProjectModel | None:
        return await self.repo.get(project_id)

    async def list_projects(self, skip: int = 0, limit: int = 50) -> tuple[list[ProjectModel], int]:
        projects = await self.repo.list_all(skip, limit)
        count = await self.repo.count()
        return projects, count

    async def update_project(self, project_id: str, data: ProjectUpdate) -> ProjectModel | None:
        return await self.repo.update(project_id, **data.model_dump(exclude_unset=True))

    async def delete_project(self, project_id: str) -> bool:
        return await self.repo.delete(project_id)
