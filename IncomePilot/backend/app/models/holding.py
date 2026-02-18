"""SQLAlchemy ORM model for portfolio holdings."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    shares: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_cost: Mapped[float] = mapped_column(Float, nullable=False)
    owner: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Venky"
    )  # Venky | Bharg
    holding_type: Mapped[str] = mapped_column(
        String(10), nullable=False, default="stock"
    )  # stock | leaps
    strike: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expiry: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    option_type: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)  # call | put
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
