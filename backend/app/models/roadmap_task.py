"""Roadmap Task database entity."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RoadmapTask(Base):
    """Actionable execution roadmap task."""

    __tablename__ = "roadmap_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    task_key: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # e.g., TSK-01
    milestone: Mapped[str] = mapped_column(String(50), nullable=False)  # 30-day, 60-day, 90-day
    stage: Mapped[str] = mapped_column(String(100), default="Research & Validation", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)  # not_started, in_progress, completed, blocked

    estimated_effort_days: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    start_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    dependencies_json: Mapped[List[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)

    deliverable: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_risk: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kpi: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="roadmap_tasks")
    user: Mapped["User"] = relationship("User")
