"""Generation routes - trigger CD generation pipeline."""
from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.revision_repo import RevisionRepository
from app.schemas.generation import GenerationConfig, GenerationRequest, GenerationStatus
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("/{project_id}/generate", response_model=GenerationStatus)
async def generate_cd(
    project_id: str,
    request: GenerationRequest = GenerationRequest(),
    db: AsyncSession = Depends(get_db),
):
    # Verify project exists
    svc = ProjectService(db)
    project = await svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest requirements
    repo = RevisionRepository(db)
    refs = await repo.list_input_refs(project_id)
    requirements_data = None

    for ref in refs:
        if ref.ref_type in ("json", "text") and ref.metadata_json:
            try:
                meta = json.loads(ref.metadata_json)
                if ref.ref_type == "json":
                    requirements_data = meta
                else:
                    requirements_data = meta.get("text", "")
            except json.JSONDecodeError:
                continue

    if not requirements_data:
        # Use demo requirements as fallback
        requirements_data = {
            "project_name": project.name,
            "rooms": [
                {"name": "Room 1", "function": "living", "area": 20},
                {"name": "Room 2", "function": "bedroom", "area": 15},
            ],
        }

    gen_svc = GenerationService(db)
    result = await gen_svc.generate(project_id, requirements_data, request.config)

    return GenerationStatus(
        revision_id=result["revision_id"],
        status=result["status"],
        progress=1.0,
        message="Generation complete",
        artifacts_count=result["artifacts_count"],
        qc_issues_count=result["qc_issues_count"],
    )


@router.get("/{project_id}/revisions")
async def list_revisions(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = RevisionRepository(db)
    revisions = await repo.list_by_project(project_id)
    return {
        "revisions": [
            {
                "id": r.id,
                "revision_number": r.revision_number,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in revisions
        ]
    }
