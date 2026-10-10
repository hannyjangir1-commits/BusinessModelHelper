"""Project management API endpoints."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMetadata
from app.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from app.services.project_service import (
    create_project,
    delete_project,
    get_project_response,
    get_user_projects,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
def create_new_project(
    data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Create a new business project."""
    project = create_project(db, current_user, data)
    return ApiResponse(data=project, message="Project created successfully")


@router.get("", response_model=PaginatedResponse[ProjectResponse])
def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for name or idea"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProjectResponse]:
    """Retrieve paginated projects owned by the authenticated user."""
    items, total_count = get_user_projects(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        industry=industry,
    )
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    return PaginatedResponse(
        items=items,
        pagination=PaginationMetadata(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get("/{project_id}", response_model=ApiResponse[ProjectResponse])
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Get project details by ID with strict ownership validation."""
    project = get_project_response(db, current_user, project_id)
    return ApiResponse(data=project)


@router.patch("/{project_id}", response_model=ApiResponse[ProjectResponse])
def update_project_details(
    project_id: str,
    data: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectResponse]:
    """Update project details."""
    updated = update_project(db, current_user, project_id, data)
    return ApiResponse(data=updated, message="Project updated successfully")


@router.delete("/{project_id}", response_model=ApiResponse[dict])
def remove_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Delete a project and all associated blueprints and generation runs."""
    delete_project(db, current_user, project_id)
    return ApiResponse(data={"deleted": True}, message="Project deleted successfully")
