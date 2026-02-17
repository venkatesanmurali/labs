"""SQLAlchemy ORM model for the trade journal."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, Integer, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    decision_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # sell | close | roll | hold | assign
    strike: Mapped[float] = mapped_column(Float, nullable=False)
    expiry: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    premium: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delta_at_entry: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Outcome fields (editable later)
    was_assigned: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True)
    closed_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
