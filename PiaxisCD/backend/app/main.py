from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import projects, inputs, generation, artifacts, demo

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(inputs.router, prefix="/api/projects", tags=["inputs"])
app.include_router(generation.router, prefix="/api/projects", tags=["generation"])
app.include_router(artifacts.router, prefix="/api/projects", tags=["artifacts"])
app.include_router(demo.router, prefix="/api/demo", tags=["demo"])

# Serve exported files
data_dir = settings.data_dir
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
