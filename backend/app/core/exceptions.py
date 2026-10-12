"""Domain exceptions and error models for AI Business Architect."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=404, code="NOT_FOUND", details=details)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=401, code="UNAUTHORIZED", details=details)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=403, code="FORBIDDEN", details=details)


class ProjectLimitExceededError(ForbiddenError):
    def __init__(
        self,
        message: str = "You have reached the maximum limit of 3 active projects for your account. Please delete an existing project before creating a new one.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, details=details)
        self.code = "PROJECT_LIMIT_REACHED"
        self.status_code = 403


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=409, code="CONFLICT", details=details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=422, code="VALIDATION_ERROR", details=details)


class RateLimitExceededError(AppException):
    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        retry_after: int = 60,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        dt = details or {}
        dt["retry_after"] = retry_after
        super().__init__(message=message, status_code=429, code="RATE_LIMIT_EXCEEDED", details=dt)


class AIProviderError(AppException):
    def __init__(
        self,
        message: str = "AI service temporarily unavailable",
        status_code: int = 502,
        code: str = "AI_PROVIDER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message=message, status_code=status_code, code=code, details=details)
