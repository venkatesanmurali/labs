"""SQLAlchemy ORM model for option trades (CC/CSP)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OptionTrade(Base):
    __tablename__ = "option_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    strategy_type: Mapped[str] = mapped_column(String(10), nullable=False)  # CC | CSP | STOCK
    trade_type: Mapped[str] = mapped_column(String(10), nullable=False)  # fresh | roll | sell
    strike: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    premium: Mapped[float] = mapped_column(Float, nullable=False)  # can be negative
    contracts: Mapped[float] = mapped_column(Float, nullable=False, default=1)  # fractional for stock shares
    trade_date: Mapped[str] = mapped_column(Date, nullable=False)
    owner: Mapped[str] = mapped_column(String(20), nullable=False, default="Venky")  # Venky | Bharg
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
