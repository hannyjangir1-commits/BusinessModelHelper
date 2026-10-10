"""Legal document acceptance tracking model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LegalAcceptance(Base):
    """Immutable audit record of user acceptance of legal documents."""

    __tablename__ = "legal_acceptances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # terms_and_conditions | privacy_policy
    document_version: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "2026-v1.0"
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="legal_acceptances")
