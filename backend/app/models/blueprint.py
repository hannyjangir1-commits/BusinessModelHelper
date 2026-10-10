"""Blueprint database model storing structured module outputs."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Blueprint(Base):
    """Saved blueprint version for a business project (BMC or Technology Stack)."""

    __tablename__ = "blueprints"
    __table_args__ = (
        UniqueConstraint("project_id", "module_type", "version", name="uq_project_module_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)

    module_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # business_model | technology_stack
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    content_json: Mapped[Dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="blueprints")
