"""Business Model Canvas API routes."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.blueprint import Blueprint
from app.models.user import User
from app.schemas.business_model import BMCUpdateRequest
from app.schemas.common import ApiResponse
from app.schemas.generation import BlueprintResponse, BlueprintVersionItem
from app.services.ai.generation import generate_business_model_canvas
from app.services.project_service import get_user_project_by_id

router = APIRouter(prefix="/projects/{project_id}/business-model", tags=["Business Model Canvas"])


@router.post("/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED)
def generate_bmc(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Generate or regenerate Business Model Canvas using the configured AI provider."""
    project = get_user_project_by_id(db, current_user, project_id)
    blueprint, warnings = generate_business_model_canvas(db, current_user, project)
    msg = "Business Model Canvas generated successfully."
    if warnings:
        msg += f" ({len(warnings)} advisory notes generated)"
    return ApiResponse(data=BlueprintResponse.model_validate(blueprint), message=msg)


@router.get("", response_model=ApiResponse[BlueprintResponse])
def get_latest_or_version_bmc(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific version number; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Retrieve saved Business Model Canvas blueprint for a project."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    query = select(Blueprint).where(
        Blueprint.project_id == project_id,
        Blueprint.module_type == "business_model",
    )
    if version is not None:
        query = query.where(Blueprint.version == version)
    else:
        query = query.order_by(desc(Blueprint.version))

    blueprint = db.execute(query).scalars().first()
    if not blueprint:
        raise NotFoundError("No Business Model Canvas blueprint found for this project.")

    return ApiResponse(data=BlueprintResponse.model_validate(blueprint))


@router.get("/versions", response_model=ApiResponse[List[BlueprintVersionItem]])
def list_bmc_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BlueprintVersionItem]]:
    """List all saved Business Model Canvas version numbers and timestamps."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    blueprints = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "business_model",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().all()

    items = [BlueprintVersionItem.model_validate(b) for b in blueprints]
    return ApiResponse(data=items)


@router.patch("", response_model=ApiResponse[BlueprintResponse])
def update_bmc_content(
    project_id: str,
    update_data: BMCUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Edit and save individual blocks or entire Business Model Canvas."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    latest = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "business_model",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    if not latest:
        raise NotFoundError("Cannot edit Business Model Canvas before generating an initial version.")

    latest.content_json = update_data.content.model_dump()
    latest.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(latest)
    return ApiResponse(data=BlueprintResponse.model_validate(latest), message="Canvas updated and saved successfully.")
