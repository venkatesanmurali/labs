"""Export service - artifact retrieval and download."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.revision_repo import RevisionRepository


class ExportService:
    def __init__(self, db: AsyncSession):
        self.repo = RevisionRepository(db)

    async def get_artifacts(self, revision_id: str) -> list:
        return await self.repo.list_artifacts(revision_id)

    async def get_qc_issues(self, revision_id: str) -> list:
        return await self.repo.list_qc_issues(revision_id)

    async def get_zip_path(self, revision_id: str) -> Path | None:
        artifacts = await self.repo.list_artifacts(revision_id)
        for a in artifacts:
            if a.artifact_type == "zip":
                path = Path(a.file_path)
                if path.exists():
                    return path
        return None
