"""Artifact retrieval and download routes."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.revision_repo import RevisionRepository
from app.schemas.export import ArtifactResponse, ExportManifestResponse, QCIssueResponse

router = APIRouter()


@router.get("/{project_id}/revisions/{revision_id}/artifacts")
async def list_artifacts(
    project_id: str,
    revision_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    artifacts = await repo.list_artifacts(revision_id)
    return {
        "artifacts": [
            ArtifactResponse.model_validate(a) for a in artifacts
        ]
    }


@router.get("/{project_id}/revisions/{revision_id}/qc-issues")
async def list_qc_issues(
    project_id: str,
    revision_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    issues = await repo.list_qc_issues(revision_id)
    return {
        "qc_issues": [QCIssueResponse.model_validate(i) for i in issues]
    }


@router.get("/{project_id}/revisions/{revision_id}/download")
async def download_package(
    project_id: str,
    revision_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    artifacts = await repo.list_artifacts(revision_id)

    zip_artifact = next((a for a in artifacts if a.artifact_type == "zip"), None)
    if not zip_artifact:
        raise HTTPException(status_code=404, detail="No zip package found")

    path = Path(zip_artifact.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(path),
        filename=zip_artifact.filename,
        media_type="application/zip",
    )


@router.get("/{project_id}/revisions/{revision_id}/artifacts/{artifact_id}/download")
async def download_artifact(
    project_id: str,
    revision_id: str,
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    artifacts = await repo.list_artifacts(revision_id)
    artifact = next((a for a in artifacts if a.id == artifact_id), None)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    path = Path(artifact.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_types = {
        "dxf": "application/dxf",
        "ifc": "application/x-step",
        "pdf": "application/pdf",
        "png": "image/png",
        "zip": "application/zip",
    }

    return FileResponse(
        path=str(path),
        filename=artifact.filename,
        media_type=media_types.get(artifact.artifact_type, "application/octet-stream"),
    )
