"""Financial Model database entity."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FinancialModel(Base):
    """Stores financial model assumptions, deterministic projections, and scenarios."""

    __tablename__ = "financial_models"
    __table_args__ = (
        UniqueConstraint("project_id", "version", name="uq_project_financial_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(150), default="Base Financial Plan", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    forecast_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)

    assumptions_json: Mapped[Dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    projections_json: Mapped[Dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    scenarios_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="financial_models")
    user: Mapped["User"] = relationship("User")
