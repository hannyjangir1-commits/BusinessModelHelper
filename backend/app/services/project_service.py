"""Project service managing project creation, ownership verification, search, and lifecycle."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.blueprint import Blueprint
from app.models.project import Project
from app.models.roadmap_task import RoadmapTask
from app.models.user import User
from app.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest


def _map_project_response(project: Project, db: Session) -> ProjectResponse:
    """Helper to compute module existence and latest versions for a project."""
    blueprints = db.execute(
        select(Blueprint.module_type, func.max(Blueprint.version))
        .where(Blueprint.project_id == project.id)
        .group_by(Blueprint.module_type)
    ).all()

    bp_map = {row[0]: row[1] for row in blueprints}

    resp = ProjectResponse.model_validate(project)
    resp.has_business_model = "business_model" in bp_map
    resp.has_technology_stack = "technology_stack" in bp_map
    resp.has_validator_report = "validator_report" in bp_map
    resp.has_market_research = "market_research" in bp_map
    resp.latest_bmc_version = bp_map.get("business_model")
    resp.latest_tech_version = bp_map.get("technology_stack")
    resp.has_financial_model = False

    has_roadmap = (
        db.execute(
            select(func.count(RoadmapTask.id)).where(RoadmapTask.project_id == project.id)
        ).scalar_one()
        > 0
    )
    resp.has_roadmap = has_roadmap

    return resp


def create_project(db: Session, user: User, data: ProjectCreateRequest) -> ProjectResponse:
    """Create a new project owned by the user."""
    project = Project(
        user_id=user.id,
        name=data.name,
        idea_description=data.idea_description,
        industry=data.industry,
        business_stage=data.business_stage,
        target_market=data.target_market,
        target_audience=data.target_audience,
        budget_amount=data.budget_amount,
        budget_currency=data.budget_currency.upper(),
        team_size=data.team_size,
        technical_preferences=data.technical_preferences,
        constraints=data.constraints,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _map_project_response(project, db)


def get_user_projects(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    industry: Optional[str] = None,
) -> Tuple[List[ProjectResponse], int]:
    """Retrieve paginated list of projects owned by the user."""
    query = select(Project).where(Project.user_id == user.id)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Project.name.ilike(search_term),
                Project.idea_description.ilike(search_term),
                Project.industry.ilike(search_term),
            )
        )

    if industry:
        query = query.where(Project.industry.ilike(f"%{industry.strip()}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar_one()

    # Pagination and sorting
    offset = (page - 1) * page_size
    query = query.order_by(desc(Project.updated_at)).offset(offset).limit(page_size)

    projects = db.execute(query).scalars().all()
    results = [_map_project_response(p, db) for p in projects]
    return results, total_count


def get_user_project_by_id(db: Session, user: User, project_id: str) -> Project:
    """Retrieve a project and strictly verify user ownership."""
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user.id)
    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found.")
    return project


def get_project_response(db: Session, user: User, project_id: str) -> ProjectResponse:
    """Get validated ProjectResponse for a project."""
    project = get_user_project_by_id(db, user, project_id)
    return _map_project_response(project, db)


def update_project(db: Session, user: User, project_id: str, data: ProjectUpdateRequest) -> ProjectResponse:
    """Update project fields for an owned project."""
    project = get_user_project_by_id(db, user, project_id)

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        if val is not None:
            if field == "budget_currency":
                val = val.upper()
            setattr(project, field, val)

    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return _map_project_response(project, db)


def delete_project(db: Session, user: User, project_id: str) -> None:
    """Delete a project and all associated cascades."""
    project = get_user_project_by_id(db, user, project_id)
    db.delete(project)
    db.commit()
