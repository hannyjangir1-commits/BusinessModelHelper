"""Common schemas and response wrappers."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard success API response envelope."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApiErrorResponse(BaseModel):
    """Standard error API response envelope."""
    success: bool = False
    error: ErrorDetail


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    items: List[T]
    pagination: PaginationMetadata
