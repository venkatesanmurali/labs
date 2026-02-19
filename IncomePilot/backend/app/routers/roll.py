"""Roll decision endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.engines.roll_engine import evaluate_roll
from app.models.strategy_config import StrategyConfig
from app.providers import get_provider
from app.schemas.roll import RollDecision, RollRequest

router = APIRouter(prefix="/api/roll", tags=["roll"])


@router.post("", response_model=RollDecision)
def roll_decision(req: RollRequest, db: Session = Depends(get_db)):
    cfg = db.query(StrategyConfig).filter_by(profile_name="default").first()
    provider = get_provider()
    settings = get_settings()

    kwargs: dict = {
        "deep_itm_ratio": settings.deep_itm_ratio,
        "gamma_zone_dte": settings.gamma_zone_dte,
    }
    if cfg:
        kwargs.update(
            target_delta_min=cfg.target_delta_min,
            target_delta_max=cfg.target_delta_max,
            roll_max_debit=cfg.roll_max_debit,
        )

    return evaluate_roll(req, provider, **kwargs)
