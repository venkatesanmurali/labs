"""
IncomePilot – FastAPI application entry-point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import (
    holdings_router,
    journal_router,
    market_data_router,
    recommendations_router,
    roll_router,
    strategy_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    init_db()
    yield


app = FastAPI(
    title="IncomePilot",
    description="Decision-intelligence for covered-call income investors.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(holdings_router)
app.include_router(recommendations_router)
app.include_router(roll_router)
app.include_router(journal_router)
app.include_router(strategy_router)
app.include_router(market_data_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "IncomePilot"}
