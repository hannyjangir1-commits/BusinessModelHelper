"""Authentication service managing registration, credentials, sessions, and security."""

from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import ConflictError, RateLimitExceededError, UnauthorizedError, ValidationError
from app.core.rate_limiting import login_rate_limiter, registration_rate_limiter
from app.core.security import generate_csrf_token, hash_password, validate_password_strength, verify_password
from app.core.sessions import create_session_token
from app.models.legal_acceptance import LegalAcceptance
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, UserLoginRequest, UserRegisterRequest

LEGAL_DOC_VERSION = "2026-v1.0"


def register_user(db: Session, request: UserRegisterRequest, client_ip: str = "127.0.0.1") -> Tuple[User, str, str]:
    """Register a new user, record legal consent, and generate initial session.

    Returns (user, session_token, csrf_token).
    """
    # Registration abuse rate check with bounded key
    rate_key = f"reg:{client_ip}"
    limited, retry_after = registration_rate_limiter.is_rate_limited(rate_key, max_attempts=10, window_seconds=3600, db=db)
    if limited:
        raise RateLimitExceededError("Too many registration attempts. Please try again later.", retry_after=retry_after)

    # Password complexity check
    valid, msg = validate_password_strength(request.password)
    if not valid:
        raise ValidationError(msg)

    # Check username or email uniqueness with a unified error to avoid enumeration
    existing_user = db.execute(
        select(User).where(
            or_(
                User.username == request.username,
                User.email == request.email,
            )
        )
    ).scalar_one_or_none()
    if existing_user:
        raise ConflictError("Username or email is already taken. Please choose different details or sign in.")

    hashed = hash_password(request.password)
    user = User(
        username=request.username,
        email=request.email,
        password_hash=hashed,
        display_name=request.username,
        preferred_currency="USD",
        is_active=True,
    )
    db.add(user)
    db.flush()  # populate user.id

    # Record mandatory legal acceptances
    terms_acceptance = LegalAcceptance(
        user_id=user.id,
        document_type="terms_and_conditions",
        document_version=LEGAL_DOC_VERSION,
    )
    privacy_acceptance = LegalAcceptance(
        user_id=user.id,
        document_type="privacy_policy",
        document_version=LEGAL_DOC_VERSION,
    )
    db.add(terms_acceptance)
    db.add(privacy_acceptance)
    db.commit()
    db.refresh(user)

    csrf_token = generate_csrf_token()
    session_token = create_session_token(user.id, csrf_token=csrf_token)
    return user, session_token, csrf_token


def authenticate_user(
    db: Session,
    request: UserLoginRequest,
    client_ip: str = "127.0.0.1",
) -> Tuple[User, str, str]:
    """Authenticate credentials against database with rate limiting configured from settings.

    Returns (user, session_token, csrf_token).
    """
    settings = get_settings()
    normalized_identifier = request.username_or_email.strip().lower()[:100]
    rate_key = f"login:{client_ip}:{normalized_identifier}"
    limited, retry_after = login_rate_limiter.is_rate_limited(
        rate_key,
        max_attempts=settings.login_rate_limit_max_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
        db=db,
    )
    if limited:
        raise RateLimitExceededError(
            "Too many failed login attempts. Please wait before trying again.",
            retry_after=retry_after,
        )

    identifier = request.username_or_email
    stmt = select(User).where(
        or_(
            User.username == identifier,
            User.email == identifier,
        )
    )
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise UnauthorizedError("Invalid username/email or password.")

    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated.")

    # Reset rate limit tracker on successful authentication
    login_rate_limiter.reset(rate_key, db=db)


    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    csrf_token = generate_csrf_token()
    session_token = create_session_token(user.id, csrf_token=csrf_token)
    return user, session_token, csrf_token


def change_user_password(db: Session, user: User, request: ChangePasswordRequest) -> None:
    """Verify current password, validate new password, and update password hash."""
    if not verify_password(request.current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect.")

    valid, msg = validate_password_strength(request.new_password)
    if not valid:
        raise ValidationError(msg)

    user.password_hash = hash_password(request.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()


def delete_user_account(db: Session, user: User, password: str) -> None:
    """Verify password and delete user account with all associated cascade records."""
    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect.")

    db.delete(user)
    db.commit()
