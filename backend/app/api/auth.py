"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.sessions import clear_session_cookie, decode_session_token, set_session_cookie
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_and_session
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
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Log out the current user, revoke the server session, and clear the session cookie."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):].strip()

    if token:
        payload = decode_session_token(token)
        if payload and "session_id" in payload and "user_id" in payload:
            from app.core.sessions import revoke_session
            revoke_session(db, user_id=payload["user_id"], session_id=payload["session_id"])

    clear_session_cookie(response)
    return ApiResponse(data={"logged_out": True}, message="Successfully logged out")


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_current_authenticated_user(
    response: Response,
    auth_data: tuple[User, dict] = Depends(get_current_user_and_session),
) -> ApiResponse[UserResponse]:
    """Retrieve details of currently authenticated user and refresh CSRF token."""
    user, payload = auth_data
    csrf_val = payload.get("csrf_token")
    if csrf_val:
        response.headers["X-CSRF-Token"] = csrf_val
    user_data = UserResponse.model_validate(user)
    user_data.csrf_token = csrf_val
    return ApiResponse(data=user_data)


@router.post("/change-password", response_model=ApiResponse[dict])
def change_password(
    request_data: ChangePasswordRequest,
    auth_data: tuple[User, dict] = Depends(get_current_user_and_session),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Change password for currently authenticated user and invalidate prior sessions."""
    current_user, payload = auth_data
    change_user_password(db, current_user, request_data)
    from app.core.sessions import revoke_user_prior_sessions
    revoke_user_prior_sessions(
        db,
        user_id=current_user.id,
        exempt_session_id=payload.get("session_id"),
    )
    return ApiResponse(data={"changed": True}, message="Password updated successfully")

