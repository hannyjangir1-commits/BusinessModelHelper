"""Session management using cryptographically signed cookies, CSRF protection, and server-checked revocation."""

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Response
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import generate_csrf_token


def _get_serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(
        secret_key=settings.secret_key,
        salt="aba-session-signing-v1",
    )


def create_session_token(
    user_id: str,
    csrf_token: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """Create a signed session token containing user_id, session_id, csrf_token, and created_at timestamp."""
    serializer = _get_serializer()
    payload = {
        "user_id": user_id,
        "session_id": session_id or str(uuid.uuid4()),
        "csrf_token": csrf_token or generate_csrf_token(),
        "created_at": time.time(),
    }
    return serializer.dumps(payload)


def decode_session_token(token: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Decode and verify signature and expiration of a session token.
    
    Rejects malformed signed payloads, including payloads missing the CSRF token,
    session_id, or user_id.
    """
    if not token or not isinstance(token, str):
        return None
    settings = get_settings()
    max_age_seconds = max_age if max_age is not None else settings.session_max_age_seconds
    serializer = _get_serializer()
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        if not isinstance(data, dict):
            return None

        user_id = data.get("user_id")
        session_id = data.get("session_id")
        csrf_token = data.get("csrf_token")

        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            return None
        if not session_id or not isinstance(session_id, str) or not session_id.strip():
            return None
        if not csrf_token or not isinstance(csrf_token, str) or not csrf_token.strip():
            return None

        return data
    except (BadSignature, SignatureExpired):
        return None


def revoke_session(db: Session, user_id: str, session_id: str) -> None:
    """Revoke a specific session token in the database (used upon user logout)."""
    from app.models.security import RevokedSession

    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.session_max_age_seconds)

    revocation = RevokedSession(
        user_id=user_id,
        session_id=session_id,
        revoked_before=None,
        exempt_session_id=None,
        created_at=now,
        expires_at=expires_at,
    )
    db.add(revocation)
    try:
        db.commit()
    except Exception:
        db.rollback()


def revoke_user_prior_sessions(
    db: Session,
    user_id: str,
    exempt_session_id: Optional[str] = None,
) -> None:
    """Invalidate all prior sessions for a user (used upon password change).
    
    Optionally exempts the current session_id to maintain the active authenticated context.
    """
    from app.models.security import RevokedSession

    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.session_max_age_seconds)

    revocation = RevokedSession(
        user_id=user_id,
        session_id=None,
        revoked_before=now,
        exempt_session_id=exempt_session_id,
        created_at=now,
        expires_at=expires_at,
    )
    db.add(revocation)
    try:
        db.commit()
    except Exception:
        db.rollback()


def is_session_revoked(
    db: Session,
    user_id: str,
    session_id: str,
    token_created_at: Optional[float] = None,
) -> bool:
    """Verify whether a session or token has been revoked on the server."""
    from app.models.security import RevokedSession

    now = datetime.now(timezone.utc)
    stmt = select(RevokedSession).where(
        RevokedSession.expires_at > now,
        or_(
            RevokedSession.session_id == session_id,
            RevokedSession.user_id == user_id,
        ),
    )
    revocations = db.execute(stmt).scalars().all()

    for rev in revocations:
        # 1. Exact session ID revocation
        if rev.session_id and rev.session_id == session_id:
            return True

        # 2. User-wide invalidation (e.g. password change)
        if rev.revoked_before is not None and rev.user_id == user_id:
            if rev.exempt_session_id and rev.exempt_session_id == session_id:
                continue
            if token_created_at is None:
                return True
            rev_dt = rev.revoked_before
            if rev_dt.tzinfo is None:
                rev_dt = rev_dt.replace(tzinfo=timezone.utc)
            token_dt = datetime.fromtimestamp(token_created_at, timezone.utc)
            if token_dt <= rev_dt:
                return True


    return False


def set_session_cookie(response: Response, token: str) -> None:
    """Set secure HTTP-only session cookie on the response."""
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        expires=settings.session_max_age_seconds,
        httponly=True,
        secure=settings.session_https_only,
        samesite=settings.session_same_site,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Clear session cookie on logout."""
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        domain=None,
        httponly=True,
        secure=settings.session_https_only,
        samesite=settings.session_same_site,
    )
