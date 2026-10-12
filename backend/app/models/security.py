"""Security models for session revocation and distributed rate limiting."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RevokedSession(Base):
    """Server-side record of revoked session identifiers and user-level invalidation timestamps."""

    __tablename__ = "revoked_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Specific session UUID to revoke (e.g. from logout)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    # Target user ID
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    # If set, all tokens issued before this timestamp for this user are invalidated (e.g. on password change)
    revoked_before: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Session ID exempt from the revoked_before invalidation (keeps the password-changing session active)
    exempt_session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # Timestamp when revocation was recorded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    # Expiration time for this revocation entry (entries past expiration can be cleaned up)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


class RateLimitEntry(Base):
    """PostgreSQL-backed rate limiting record to coordinate limits across multi-instance deployments."""

    __tablename__ = "rate_limit_entries"

    # Rate limiting key (e.g. "login:127.0.0.1:alice", "gen:user-uuid")
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    window_start: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
