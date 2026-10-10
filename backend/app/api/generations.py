"""Generation audit history API routes."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.generation import GenerationRun
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.generation import GenerationRunResponse
from app.services.project_service import get_user_project_by_id

router = APIRouter(tags=["Generations"])


@router.get("/projects/{project_id}/generations", response_model=ApiResponse[List[GenerationRunResponse]])
def get_project_generation_history(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[GenerationRunResponse]]:
    """Retrieve audit history of all generation attempts for a project."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership

    runs = db.execute(
        select(GenerationRun)
        .where(GenerationRun.project_id == project_id)
        .order_by(desc(GenerationRun.created_at))
    ).scalars().all()

    items = [GenerationRunResponse.model_validate(r) for r in runs]
    return ApiResponse(data=items)


@router.get("/generations/{generation_id}", response_model=ApiResponse[GenerationRunResponse])
def get_single_generation_run(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[GenerationRunResponse]:
    """Retrieve a single generation run record with ownership verification."""
    run = db.execute(
        select(GenerationRun).where(
            GenerationRun.id == generation_id,
            GenerationRun.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not run:
        raise NotFoundError("Generation run record not found.")

    return ApiResponse(data=GenerationRunResponse.model_validate(run))
