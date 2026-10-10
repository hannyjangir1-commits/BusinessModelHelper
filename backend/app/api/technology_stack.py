"""Technology Stack Recommendation API routes."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import check_generation_rate_limit, get_current_user
from app.models.blueprint import Blueprint
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.generation import BlueprintResponse, BlueprintVersionItem
from app.schemas.technology_stack import TechStackUpdateRequest
from app.services.ai.generation import generate_technology_stack
from app.services.project_service import get_user_project_by_id

router = APIRouter(prefix="/projects/{project_id}/technology-stack", tags=["Technology Stack"])


@router.post("/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED)
def generate_tech_stack(
    project_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(check_generation_rate_limit),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Generate or regenerate Technology Stack Recommendation using configured AI provider."""
    project = get_user_project_by_id(db, current_user, project_id)
    blueprint, warnings = generate_technology_stack(db, current_user, project)
    msg = "Technology Stack recommendation generated successfully."
    if warnings:
        msg += f" ({len(warnings)} advisory notes generated)"
    return ApiResponse(data=BlueprintResponse.model_validate(blueprint), message=msg)


@router.get("", response_model=ApiResponse[BlueprintResponse])
def get_latest_or_version_tech_stack(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific version number; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Retrieve saved Technology Stack blueprint for a project."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    query = select(Blueprint).where(
        Blueprint.project_id == project_id,
        Blueprint.module_type == "technology_stack",
    )
    if version is not None:
        query = query.where(Blueprint.version == version)
    else:
        query = query.order_by(desc(Blueprint.version))

    blueprint = db.execute(query).scalars().first()
    if not blueprint:
        raise NotFoundError("No Technology Stack blueprint found for this project.")

    return ApiResponse(data=BlueprintResponse.model_validate(blueprint))


@router.get("/versions", response_model=ApiResponse[List[BlueprintVersionItem]])
def list_tech_stack_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BlueprintVersionItem]]:
    """List all saved Technology Stack version numbers and timestamps."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    blueprints = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "technology_stack",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().all()

    items = [BlueprintVersionItem.model_validate(b) for b in blueprints]
    return ApiResponse(data=items)


@router.patch("", response_model=ApiResponse[BlueprintResponse])
def update_tech_stack_content(
    project_id: str,
    update_data: TechStackUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Edit and save individual recommendations or entire Technology Stack blueprint."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    latest = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "technology_stack",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    if not latest:
        raise NotFoundError("Cannot edit Technology Stack before generating an initial version.")

    latest.content_json = update_data.content.model_dump()
    latest.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(latest)
    return ApiResponse(data=BlueprintResponse.model_validate(latest), message="Technology Stack updated and saved successfully.")
