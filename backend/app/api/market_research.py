"""Market and Competitor Research API endpoints."""

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
from app.schemas.market_research import MarketResearchUpdateRequest
from app.services.project_service import get_user_project_by_id
from app.services.research.research_pipeline import generate_market_research_report

router = APIRouter(tags=["Market Research"])


@router.post("/projects/{project_id}/market-research/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED)
@router.post("/projects/{project_id}/research/generate", response_model=ApiResponse[BlueprintResponse], status_code=status.HTTP_201_CREATED)
def generate_research(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Execute live market and competitor research with verified source citations."""
    project = get_user_project_by_id(db, current_user, project_id)
    blueprint, warnings = generate_market_research_report(db, current_user, project)
    msg = "Market and competitor research completed successfully."
    if warnings:
        msg += f" ({', '.join(warnings)})"
    return ApiResponse(data=BlueprintResponse.model_validate(blueprint), message=msg)


@router.get("/projects/{project_id}/market-research", response_model=ApiResponse[BlueprintResponse])
@router.get("/projects/{project_id}/research", response_model=ApiResponse[BlueprintResponse])
def get_latest_or_version_research(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific version number; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Retrieve saved market research report."""
    get_user_project_by_id(db, current_user, project_id)

    query = select(Blueprint).where(
        Blueprint.project_id == project_id,
        Blueprint.module_type == "market_research",
    )
    if version is not None:
        query = query.where(Blueprint.version == version)
    else:
        query = query.order_by(desc(Blueprint.version))

    blueprint = db.execute(query).scalars().first()
    if not blueprint:
        raise NotFoundError("No market research report found for this project.")

    return ApiResponse(data=BlueprintResponse.model_validate(blueprint))


@router.get("/projects/{project_id}/market-research/versions", response_model=ApiResponse[List[BlueprintVersionItem]])
@router.get("/projects/{project_id}/research/versions", response_model=ApiResponse[List[BlueprintVersionItem]])
def list_research_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[BlueprintVersionItem]]:
    """List all saved market research report versions."""
    get_user_project_by_id(db, current_user, project_id)

    blueprints = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "market_research",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().all()

    return ApiResponse(data=[BlueprintVersionItem.model_validate(b) for b in blueprints])


@router.patch("/projects/{project_id}/market-research", response_model=ApiResponse[BlueprintResponse])
@router.patch("/projects/{project_id}/research", response_model=ApiResponse[BlueprintResponse])
def update_research_content(
    project_id: str,
    update_data: MarketResearchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BlueprintResponse]:
    """Manually update or refine competitor profiles and research data."""
    get_user_project_by_id(db, current_user, project_id)

    latest = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "market_research",
        )
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    if not latest:
        raise NotFoundError("Cannot edit research report before generating an initial version.")

    latest.content_json = update_data.content.model_dump()
    latest.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(latest)
    return ApiResponse(data=BlueprintResponse.model_validate(latest), message="Research report updated successfully.")
