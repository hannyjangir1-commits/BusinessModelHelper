"""AI Business Idea Validator API endpoints."""

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
from app.schemas.common import ApiResponse
from app.schemas.generation import BlueprintResponse, BlueprintVersionItem
from app.schemas.validator import ValidationUpdateRequest
from app.services.ai.validator_pipeline import generate_validation_report
from app.services.project_service import get_user_project_by_id

router = APIRouter(tags=["Idea Validator"])


@router.post("/projects/{project_id}/validator/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED)
@router.post("/projects/{project_id}/validation/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED, include_in_schema=False)
def generate_validator_report(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Generate or regenerate AI Business Idea Validation report."""
    project = get_user_project_by_id(db, current_user, project_id)
    blueprint, warnings = generate_validation_report(db, current_user, project)
    msg = "Idea validation report generated successfully."
    if warnings:
        msg += f" ({len(warnings)} strategic notes flagged)"
    return ApiResponse(data=BlueprintResponse.model_validate(blueprint), message=msg)


@router.get("/projects/{project_id}/validator", response_model=ApiResponse[BlueprintResponse])
@router.get("/projects/{project_id}/validation", response_model=ApiResponse[BlueprintResponse], include_in_schema=False)
def get_latest_or_version_validation(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific version number; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Retrieve saved validation report for project."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    query = select(Blueprint).where(
        Blueprint.project_id == project_id,
        Blueprint.module_type == "validation_report",
    )
    if version is not None:
        query = query.where(Blueprint.version == version)
    else:
        query = query.order_by(desc(Blueprint.version))

    blueprint = db.execute(query).scalars().first()
    if not blueprint:
        raise NotFoundError("No validation report found for this project.")

    return ApiResponse(data=BlueprintResponse.model_validate(blueprint))


@router.get("/projects/{project_id}/validator/versions", response_model=ApiResponse[List[BlueprintVersionItem]])
@router.get("/projects/{project_id}/validation/versions", response_model=ApiResponse[List[BlueprintVersionItem]], include_in_schema=False)
def list_validation_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BlueprintVersionItem]]:
    """List all saved validation report versions."""
    get_user_project_by_id(db, current_user, project_id)

    blueprints = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "validation_report",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().all()

    return ApiResponse(data=[BlueprintVersionItem.model_validate(b) for b in blueprints])


@router.patch("/projects/{project_id}/validator", response_model=ApiResponse[BlueprintResponse])
@router.patch("/projects/{project_id}/validation", response_model=ApiResponse[BlueprintResponse], include_in_schema=False)
def update_validation_report_content(
    project_id: str,
    update_data: ValidationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Edit and save manual refinements to the latest validation report."""
    get_user_project_by_id(db, current_user, project_id)

    latest = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "validation_report",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    if not latest:
        raise NotFoundError("Cannot edit validation report before generating an initial version.")

    latest.content_json = update_data.content.model_dump()
    latest.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(latest)
    return ApiResponse(data=BlueprintResponse.model_validate(latest), message="Validation report updated successfully.")
