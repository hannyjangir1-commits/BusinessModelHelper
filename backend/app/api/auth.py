"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.sessions import clear_session_cookie, set_session_cookie
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import authenticate_user, change_user_password, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[AuthResponse], status_code=status.HTTP_201_CREATED)
def register(
    request_data: UserRegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> ApiResponse[AuthResponse]:
    """Register a new user account with accepted terms and privacy policy."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user, session_token, csrf_token = register_user(db, request_data, client_ip=client_ip)
    set_session_cookie(response, session_token)
    return ApiResponse(
        data=AuthResponse(
            user=UserResponse.model_validate(user),
            csrf_token=csrf_token,
            message="Account registered successfully",
        ),
        message="Registration successful",
    )


@router.post("/login", response_model=ApiResponse[AuthResponse])
def login(
    request_data: UserLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> ApiResponse[AuthResponse]:
    """Authenticate with username or email and password."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user, session_token, csrf_token = authenticate_user(db, request_data, client_ip=client_ip)
    set_session_cookie(response, session_token)
    return ApiResponse(
        data=AuthResponse(
            user=UserResponse.model_validate(user),
            csrf_token=csrf_token,
            message="Login successful",
        ),
        message="Login successful",
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(response: Response) -> ApiResponse[dict]:
    """Log out the current user and invalidate the session cookie."""
    clear_session_cookie(response)
    return ApiResponse(data={"logged_out": True}, message="Successfully logged out")


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_current_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[UserResponse]:
    """Retrieve details of currently authenticated user."""
    return ApiResponse(data=UserResponse.model_validate(current_user))


@router.post("/change-password", response_model=ApiResponse[dict])
def change_password(
    request_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Change password for currently authenticated user."""
    change_user_password(db, current_user, request_data)
    return ApiResponse(data={"changed": True}, message="Password updated successfully")
