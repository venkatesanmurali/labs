"""SQLAlchemy model for QC issues."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QCIssueModel(Base):
    __tablename__ = "qc_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("revisions.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="warning")  # error, warning, info
    category: Mapped[str] = mapped_column(String(50), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    element_id: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    revision = relationship("RevisionModel", back_populates="qc_issues")
