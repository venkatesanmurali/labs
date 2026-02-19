"""SQLAlchemy model for generated artifacts."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("revisions.id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(50), default="")  # dxf, ifc, pdf, png, zip
    filename: Mapped[str] = mapped_column(String(255), default="")
    file_path: Mapped[str] = mapped_column(Text, default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    sheet_number: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    revision = relationship("RevisionModel", back_populates="artifacts")
