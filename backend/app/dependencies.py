"""FastAPI dependencies for authentication, database sessions, and CSRF protection."""

from typing import Optional
from fastapi import Cookie, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.sessions import decode_session_token
from app.database import get_db
from app.models.user import User


def get_current_user_and_session(
    request: Request,
    db: Session = Depends(get_db),
) -> tuple[User, dict]:
    """Retrieve current authenticated user and session payload from cookie or bearer header."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)

    # Support Authorization header for programmatic testing or clients
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):].strip()

    if not token:
        raise UnauthorizedError("Authentication required. Please log in.")

    payload = decode_session_token(token)
    if not payload or "user_id" not in payload:
        raise UnauthorizedError("Session expired or invalid. Please log in again.")

    user = db.execute(select(User).where(User.id == payload["user_id"])).scalar_one_or_none()
    if not user:
        raise UnauthorizedError("User account no longer exists.")
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated.")

    return user, payload


def get_current_user(
    auth_data: tuple[User, dict] = Depends(get_current_user_and_session),
) -> User:
    """Dependency that returns the authenticated User entity."""
    user, _ = auth_data
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional authentication dependency; returns None if unauthenticated."""
    try:
        user, _ = get_current_user_and_session(request, db)
        return user
    except UnauthorizedError:
        return None


def verify_csrf(
    request: Request,
    auth_data: tuple[User, dict] = Depends(get_current_user_and_session),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
) -> None:
    """Validate CSRF token on state-changing requests."""
    _, payload = auth_data
    session_csrf = payload.get("csrf_token")
    if not session_csrf or not x_csrf_token or session_csrf != x_csrf_token:
        # If running in test mode with direct auth header, bypass CSRF
        if request.headers.get("Authorization", "").startswith("Bearer "):
            return
        raise ForbiddenError("CSRF verification failed. Missing or invalid X-CSRF-Token header.")


def check_generation_rate_limit(
    current_user: User = Depends(get_current_user),
) -> None:
    """Enforce sliding-window rate limits on resource-intensive AI generation and external research."""
    from app.core.exceptions import RateLimitExceededError
    from app.core.rate_limiting import generation_rate_limiter

    rate_key = f"gen:{current_user.id}"
    limited, retry_after = generation_rate_limiter.is_rate_limited(rate_key, max_attempts=15, window_seconds=60)
    if limited:
        raise RateLimitExceededError(
            f"Generation rate limit exceeded. Please wait {retry_after}s before requesting another generation.",
            retry_after=retry_after,
        )

