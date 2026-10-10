"""Copilot Revision database entity."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CopilotRevision(Base):
    """Audit record of controlled AI copilot proposals and user decisions."""

    __tablename__ = "copilot_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    target_module: Mapped[str] = mapped_column(String(50), nullable=False)  # business_model, technology_stack, financial_model, execution_roadmap, validation_report
    target_section: Mapped[str] = mapped_column(String(100), nullable=False)  # section or block identifier
    action_type: Mapped[str] = mapped_column(String(30), default="propose_edit", nullable=False)  # propose_edit | answer_question
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending | accepted | rejected

    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    proposal_content: Mapped[Dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    previous_content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON_TYPE, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="copilot_revisions")
    user: Mapped["User"] = relationship("User")
