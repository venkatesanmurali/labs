"""Input reference routes - image upload, calibration, requirements."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.repositories.revision_repo import RevisionRepository
from app.schemas.calibration import CalibrationInput, CalibrationResponse
from app.schemas.requirements import RequirementsInput, RequirementsTextInput

router = APIRouter()


@router.post("/{project_id}/inputs/images")
async def upload_image(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)

    # Save file
    upload_dir = settings.data_dir / project_id / "inputs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    content = await file.read()
    file_path.write_bytes(content)

    ref = await repo.add_input_ref(
        project_id=project_id,
        ref_type="image",
        filename=file.filename,
        file_path=str(file_path),
    )

    return {"id": ref.id, "filename": ref.filename, "file_path": str(file_path)}


@router.post("/{project_id}/inputs/calibrate")
async def calibrate_image(
    project_id: str,
    data: CalibrationInput,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    ref = await repo.get_input_ref(data.input_ref_id)
    if not ref:
        raise HTTPException(status_code=404, detail="Input reference not found")

    scale_factor = data.pixel_distance / data.real_distance
    ref.scale_factor = scale_factor
    await db.commit()

    return CalibrationResponse(
        input_ref_id=ref.id,
        scale_factor=scale_factor,
        unit=data.unit,
    )


@router.post("/{project_id}/inputs/requirements")
async def submit_requirements(
    project_id: str,
    data: RequirementsInput,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    ref = await repo.add_input_ref(
        project_id=project_id,
        ref_type="json",
        filename="requirements.json",
        metadata_json=data.model_dump_json(),
    )
    return {"id": ref.id, "type": "json", "rooms_count": len(data.rooms)}


@router.post("/{project_id}/inputs/requirements-text")
async def submit_requirements_text(
    project_id: str,
    data: RequirementsTextInput,
    db: AsyncSession = Depends(get_db),
):
    repo = RevisionRepository(db)
    ref = await repo.add_input_ref(
        project_id=project_id,
        ref_type="text",
        filename="requirements.txt",
        metadata_json=data.model_dump_json(),
    )
    return {"id": ref.id, "type": "text"}


@router.get("/{project_id}/inputs")
async def list_inputs(project_id: str, db: AsyncSession = Depends(get_db)):
    repo = RevisionRepository(db)
    refs = await repo.list_input_refs(project_id)
    return {"inputs": [{"id": r.id, "type": r.ref_type, "filename": r.filename} for r in refs]}
