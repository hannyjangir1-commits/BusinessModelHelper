"""Execution Roadmap API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.blueprint import Blueprint
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.generation import BlueprintResponse, BlueprintVersionItem
from app.schemas.roadmap import (
    RoadmapOverviewResponse,
    RoadmapTaskCreateRequest,
    RoadmapTaskResponse,
    RoadmapTaskUpdateRequest,
)
from app.services.project_service import get_user_project_by_id
from app.services.roadmap_service import (
    create_roadmap_task,
    delete_roadmap_task,
    generate_execution_roadmap,
    get_project_roadmap_overview,
    update_roadmap_task,
)

router = APIRouter(prefix="/projects/{project_id}/roadmap", tags=["Execution Roadmap"])


@router.post("/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED)
def generate_roadmap(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Generate intelligent 30/60/90-day execution roadmap based on project blueprint and risks."""
    project = get_user_project_by_id(db, current_user, project_id)
    blueprint, _ = generate_execution_roadmap(db, current_user, project)
    return ApiResponse(
        data=BlueprintResponse.model_validate(blueprint),
        message="Execution roadmap generated successfully.",
    )


@router.get("", response_model=ApiResponse[RoadmapOverviewResponse])
def get_roadmap_overview(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[RoadmapOverviewResponse]:
    """Retrieve full roadmap task list with milestone completion percentages."""
    overview = get_project_roadmap_overview(db, current_user, project_id)
    return ApiResponse(data=overview)


@router.post("/tasks", response_model=ApiResponse[RoadmapTaskResponse], status_code=status.HTTP_201_CREATED)
def add_new_task(
    project_id: str,
    req: RoadmapTaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[RoadmapTaskResponse]:
    """Add a custom task to the roadmap."""
    task = create_roadmap_task(db, current_user, project_id, req)
    return ApiResponse(data=task, message="Task added to roadmap successfully.")


@router.patch("/tasks/{task_id}", response_model=ApiResponse[RoadmapTaskResponse])
def edit_task(
    project_id: str,
    task_id: str,
    req: RoadmapTaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[RoadmapTaskResponse]:
    """Update task status (e.g. mark completed), priority, timing, or details."""
    task = update_roadmap_task(db, current_user, project_id, task_id, req)
    return ApiResponse(data=task, message="Task updated successfully.")


@router.delete("/tasks/{task_id}", response_model=ApiResponse[dict])
def remove_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Remove a task from the roadmap."""
    delete_roadmap_task(db, current_user, project_id, task_id)
    return ApiResponse(data={"deleted": True}, message="Task deleted successfully.")


@router.get("/versions", response_model=ApiResponse[List[BlueprintVersionItem]])
def list_roadmap_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BlueprintVersionItem]]:
    """List historical generated roadmap snapshot versions."""
    get_user_project_by_id(db, current_user, project_id)

    blueprints = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "execution_roadmap",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().all()

    return ApiResponse(data=[BlueprintVersionItem.model_validate(b) for b in blueprints])
