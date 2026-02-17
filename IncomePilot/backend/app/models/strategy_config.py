"""SQLAlchemy ORM model for per-user strategy configuration."""

from __future__ import annotations

from sqlalchemy import Float, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StrategyConfig(Base):
    __tablename__ = "strategy_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Single-user for now; add user_id FK later for multi-tenant
    profile_name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, default="default"
    )

    target_delta_min: Mapped[float] = mapped_column(Float, default=0.15)
    target_delta_max: Mapped[float] = mapped_column(Float, default=0.30)
    preferred_dte_min: Mapped[int] = mapped_column(Integer, default=7)
    preferred_dte_max: Mapped[int] = mapped_column(Integer, default=21)
    min_annualized_yield: Mapped[float] = mapped_column(Float, default=8.0)
    max_assignment_probability: Mapped[float] = mapped_column(Float, default=35.0)
    avoid_earnings_before_days: Mapped[int] = mapped_column(Integer, default=7)
    avoid_earnings_after_days: Mapped[int] = mapped_column(Integer, default=2)
    min_open_interest: Mapped[int] = mapped_column(Integer, default=100)
    min_volume: Mapped[int] = mapped_column(Integer, default=10)

    # Scoring weights
    w_yield: Mapped[float] = mapped_column(Float, default=0.35)
    w_delta_fit: Mapped[float] = mapped_column(Float, default=0.25)
    w_liquidity: Mapped[float] = mapped_column(Float, default=0.20)
    w_distance: Mapped[float] = mapped_column(Float, default=0.10)
    w_earnings_safety: Mapped[float] = mapped_column(Float, default=0.10)

    # Roll thresholds
    roll_max_debit: Mapped[float] = mapped_column(Float, default=0.50)

    created_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
