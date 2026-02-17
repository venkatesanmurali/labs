"""Strategy configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.strategy_config import StrategyConfig
from app.schemas.strategy import StrategyConfigOut, StrategyConfigUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create_default(db: Session) -> StrategyConfig:
    cfg = db.query(StrategyConfig).filter_by(profile_name="default").first()
    if not cfg:
        cfg = StrategyConfig(profile_name="default")
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("", response_model=StrategyConfigOut)
def get_settings(db: Session = Depends(get_db)):
    return _get_or_create_default(db)


@router.put("", response_model=StrategyConfigOut)
def update_settings(
    payload: StrategyConfigUpdate, db: Session = Depends(get_db)
):
    cfg = _get_or_create_default(db)
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, key, val)
    db.commit()
    db.refresh(cfg)
    return cfg
