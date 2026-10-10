"""Profile service for updating user details."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.profile import ProfileUpdateRequest


def update_user_profile(db: Session, user: User, request: ProfileUpdateRequest) -> User:
    """Update allowed profile fields safely."""
    if request.display_name is not None:
        user.display_name = request.display_name.strip()
    if request.bio is not None:
        user.bio = request.bio.strip() if request.bio else None
    if request.country is not None:
        user.country = request.country.strip() if request.country else None
    if request.preferred_currency is not None:
        user.preferred_currency = request.preferred_currency.strip().upper()

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
