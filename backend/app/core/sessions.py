"""Session management using cryptographically signed cookies and CSRF protection."""

import uuid
from typing import Any, Dict, Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Response

from app.config import get_settings
from app.core.security import generate_csrf_token


def _get_serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(
        secret_key=settings.secret_key,
        salt="aba-session-signing-v1",
    )


def create_session_token(user_id: str, csrf_token: Optional[str] = None) -> str:
    """Create a signed session token containing user_id, session_id, and csrf_token."""
    serializer = _get_serializer()
    payload = {
        "user_id": user_id,
        "session_id": str(uuid.uuid4()),
        "csrf_token": csrf_token or generate_csrf_token(),
    }
    return serializer.dumps(payload)


def decode_session_token(token: str, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Decode and verify signature and expiration of a session token."""
    if not token:
        return None
    settings = get_settings()
    max_age_seconds = max_age if max_age is not None else settings.session_max_age_seconds
    serializer = _get_serializer()
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        if isinstance(data, dict) and "user_id" in data:
            return data
        return None
    except (BadSignature, SignatureExpired):
        return None


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
