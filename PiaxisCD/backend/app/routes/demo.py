"""Demo mode endpoint - one-click sample generation."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.generation_service import DemoService

router = APIRouter()


@router.post("")
async def run_demo(seed: int = 42):
    """Run a demo generation without database. Returns results immediately."""
    result = DemoService.generate_demo(seed=seed)
    return result


@router.get("/status")
async def demo_status():
    return {"available": True, "description": "One-click demo: generates CD set for a sample residence"}
