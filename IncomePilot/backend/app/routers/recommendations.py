"""Covered-call and cash-secured-put recommendation endpoint."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.engines.recommendation_engine import recommend_covered_calls, recommend_cash_secured_puts
from app.models.strategy_config import StrategyConfig
from app.providers import get_provider
from app.schemas.recommendation import RecommendationResponse

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _load_strategy(db: Session) -> Optional[StrategyConfig]:
    return db.query(StrategyConfig).filter_by(profile_name="default").first()


@router.get("/{symbol}", response_model=RecommendationResponse)
def get_recommendations(
    symbol: str,
    strategy_type: str = Query(default="CC", pattern="^(CC|CSP)$"),
    db: Session = Depends(get_db),
):
    cfg = _load_strategy(db)
    provider = get_provider()
    settings = get_settings()

    kwargs: dict = {
        "w_theta_efficiency": settings.w_theta_efficiency,
        "w_spread": settings.w_spread,
        "liquidity_oi_threshold": settings.liquidity_oi_threshold,
        "liquidity_volume_threshold": settings.liquidity_volume_threshold,
        "distance_peak_otm": settings.distance_peak_otm,
        "distance_range": settings.distance_range,
        "spread_min_pct": settings.spread_min_pct,
        "spread_max_pct": settings.spread_max_pct,
    }
    if cfg:
        kwargs.update(
            target_delta_min=cfg.target_delta_min,
            target_delta_max=cfg.target_delta_max,
            preferred_dte_min=cfg.preferred_dte_min,
            preferred_dte_max=cfg.preferred_dte_max,
            min_annualized_yield=cfg.min_annualized_yield,
            max_assignment_prob=cfg.max_assignment_probability / 100,
            avoid_earnings_before=cfg.avoid_earnings_before_days,
            avoid_earnings_after=cfg.avoid_earnings_after_days,
            min_oi=cfg.min_open_interest,
            min_vol=cfg.min_volume,
            w_yield=cfg.w_yield,
            w_delta_fit=cfg.w_delta_fit,
            w_liquidity=cfg.w_liquidity,
            w_distance=cfg.w_distance,
            w_earnings_safety=cfg.w_earnings_safety,
        )

    if strategy_type == "CSP":
        return recommend_cash_secured_puts(symbol.upper(), provider, **kwargs)
    return recommend_covered_calls(symbol.upper(), provider, **kwargs)
