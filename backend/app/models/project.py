"""Project database model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.blueprint import Blueprint
    from app.models.generation import GenerationRun
    from app.models.financial_model import FinancialModel
    from app.models.roadmap_task import RoadmapTask
    from app.models.copilot_revision import CopilotRevision


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    """Business project entity owned by a user."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    idea_description: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    business_stage: Mapped[str] = mapped_column(String(50), default="idea", nullable=False)
    target_market: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    budget_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    budget_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    team_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    technical_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    blueprints: Mapped[List["Blueprint"]] = relationship("Blueprint", back_populates="project", cascade="all, delete-orphan")
    generation_runs: Mapped[List["GenerationRun"]] = relationship("GenerationRun", back_populates="project", cascade="all, delete-orphan")
    financial_models: Mapped[List["FinancialModel"]] = relationship("FinancialModel", back_populates="project", cascade="all, delete-orphan")
    roadmap_tasks: Mapped[List["RoadmapTask"]] = relationship("RoadmapTask", back_populates="project", cascade="all, delete-orphan")
    copilot_revisions: Mapped[List["CopilotRevision"]] = relationship("CopilotRevision", back_populates="project", cascade="all, delete-orphan")
