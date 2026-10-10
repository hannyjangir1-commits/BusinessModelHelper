"""User profile and account settings API endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.sessions import clear_session_cookie
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import ApiResponse
from app.schemas.profile import DeleteAccountRequest, ProfileUpdateRequest
from app.services.auth_service import delete_user_account
from app.services.profile_service import update_user_profile

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=ApiResponse[UserResponse])
def get_profile(current_user: User = Depends(get_current_user)) -> ApiResponse[UserResponse]:
    """Retrieve profile of the current authenticated user."""
    return ApiResponse(data=UserResponse.model_validate(current_user))


@router.patch("", response_model=ApiResponse[UserResponse])
def update_profile(
    update_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UserResponse]:
    """Update profile attributes."""
    updated = update_user_profile(db, current_user, update_data)
    return ApiResponse(data=UserResponse.model_validate(updated), message="Profile updated successfully")


@router.delete("", response_model=ApiResponse[dict])
def delete_account(
    delete_data: DeleteAccountRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Permanently delete user account and associated projects with password verification."""
    delete_user_account(db, current_user, password=delete_data.password)
    clear_session_cookie(response)
    return ApiResponse(
        data={"deleted": True},
        message="Account and associated data have been permanently deleted.",
    )
