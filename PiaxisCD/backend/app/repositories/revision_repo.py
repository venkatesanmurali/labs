"""Repository for revision and artifact operations."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactModel
from app.models.input_ref import InputRefModel
from app.models.qc_issue import QCIssueModel
from app.models.revision import RevisionModel


class RevisionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> RevisionModel:
        revision = RevisionModel(**kwargs)
        self.db.add(revision)
        await self.db.commit()
        await self.db.refresh(revision)
        return revision

    async def get(self, revision_id: str) -> RevisionModel | None:
        return await self.db.get(RevisionModel, revision_id)

    async def list_by_project(self, project_id: str) -> list[RevisionModel]:
        result = await self.db.execute(
            select(RevisionModel)
            .where(RevisionModel.project_id == project_id)
            .order_by(RevisionModel.revision_number.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, revision_id: str, status: str) -> RevisionModel | None:
        revision = await self.get(revision_id)
        if revision:
            revision.status = status
            await self.db.commit()
            await self.db.refresh(revision)
        return revision

    async def add_artifact(self, **kwargs) -> ArtifactModel:
        artifact = ArtifactModel(**kwargs)
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def list_artifacts(self, revision_id: str) -> list[ArtifactModel]:
        result = await self.db.execute(
            select(ArtifactModel).where(ArtifactModel.revision_id == revision_id)
        )
        return list(result.scalars().all())

    async def add_qc_issue(self, **kwargs) -> QCIssueModel:
        issue = QCIssueModel(**kwargs)
        self.db.add(issue)
        await self.db.commit()
        await self.db.refresh(issue)
        return issue

    async def list_qc_issues(self, revision_id: str) -> list[QCIssueModel]:
        result = await self.db.execute(
            select(QCIssueModel).where(QCIssueModel.revision_id == revision_id)
        )
        return list(result.scalars().all())

    async def add_input_ref(self, **kwargs) -> InputRefModel:
        ref = InputRefModel(**kwargs)
        self.db.add(ref)
        await self.db.commit()
        await self.db.refresh(ref)
        return ref

    async def list_input_refs(self, project_id: str) -> list[InputRefModel]:
        result = await self.db.execute(
            select(InputRefModel).where(InputRefModel.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_input_ref(self, ref_id: str) -> InputRefModel | None:
        return await self.db.get(InputRefModel, ref_id)
