"""Project service managing project creation, ownership verification, search, and lifecycle."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, or_, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.blueprint import Blueprint
from app.models.project import Project
from app.models.roadmap_task import RoadmapTask
from app.models.user import User
from app.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest

import threading
from collections import defaultdict

_project_module_locks_guard = threading.Lock()
_project_module_locks: Dict[Tuple[str, str], threading.Lock] = defaultdict(threading.Lock)


def _get_project_module_lock(project_id: str, module_type: str) -> threading.Lock:
    """Retrieve fine-grained lock for a specific project module."""
    with _project_module_locks_guard:
        return _project_module_locks[(project_id, module_type)]


def save_blueprint_version(
    db: Session,
    project_id: str,
    module_type: str,
    content_json: Dict[str, Any],
    max_retries: int = 15,
) -> Blueprint:
    """Save a new blueprint version, safely handling concurrent generation attempts.

    Uses fine-grained project/module locking and bounded retries with savepoints (db.begin_nested())
    on unique constraint collisions (uq_project_module_version) so concurrent transactions
    reliably assign distinct, monotonic versions.
    """
    import random
    import time

    lock = _get_project_module_lock(project_id, module_type)
    with lock:
        for attempt in range(max_retries):
            try:
                with db.begin_nested():
                    latest_version = db.execute(
                        select(func.coalesce(func.max(Blueprint.version), 0)).where(
                            Blueprint.project_id == project_id,
                            Blueprint.module_type == module_type,
                        )
                    ).scalar_one()
                    new_version = latest_version + 1

                    blueprint = Blueprint(
                        project_id=project_id,
                        module_type=module_type,
                        version=new_version,
                        content_json=content_json,
                    )
                    db.add(blueprint)
                    db.flush()
                    return blueprint
            except (IntegrityError, OperationalError):
                if attempt >= max_retries - 1:
                    raise
                time.sleep(random.uniform(0.03, 0.08) * (attempt + 1))

        raise RuntimeError(
            f"Failed to assign unique blueprint version for project '{project_id}' module '{module_type}' after {max_retries} attempts."
        )


def _build_project_response(
    project: Project,
    bp_map: Dict[str, int],
    has_roadmap: bool,
) -> ProjectResponse:
    """Helper to populate module status flags and versions into ProjectResponse."""
    resp = ProjectResponse.model_validate(project)
    resp.has_business_model = "business_model" in bp_map
    resp.has_technology_stack = "technology_stack" in bp_map
    resp.has_validator_report = ("validation_report" in bp_map) or ("validator_report" in bp_map)
    resp.has_market_research = "market_research" in bp_map
    resp.latest_bmc_version = bp_map.get("business_model")
    resp.latest_tech_version = bp_map.get("technology_stack")
    resp.has_financial_model = False
    resp.has_roadmap = has_roadmap
    return resp


def _map_project_response(project: Project, db: Session) -> ProjectResponse:
    """Helper to compute module existence and latest versions for a single project."""
    blueprints = db.execute(
        select(Blueprint.module_type, func.max(Blueprint.version))
        .where(Blueprint.project_id == project.id)
        .group_by(Blueprint.module_type)
    ).all()

    bp_map = {row[0]: row[1] for row in blueprints}

    has_roadmap = (
        db.execute(
            select(func.count(RoadmapTask.id)).where(RoadmapTask.project_id == project.id)
        ).scalar_one()
        > 0
    )

    return _build_project_response(project, bp_map, has_roadmap)



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
    """Retrieve paginated list of projects owned by the user with bulk summary loading."""
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
    if not projects:
        return [], total_count

    project_ids = [p.id for p in projects]

    # Bulk fetch blueprint latest versions for selected project IDs
    bp_rows = db.execute(
        select(Blueprint.project_id, Blueprint.module_type, func.max(Blueprint.version))
        .where(Blueprint.project_id.in_(project_ids))
        .group_by(Blueprint.project_id, Blueprint.module_type)
    ).all()
    bp_by_project: Dict[str, Dict[str, int]] = defaultdict(dict)
    for pid, mod, ver in bp_rows:
        bp_by_project[pid][mod] = ver

    # Bulk fetch roadmap task counts for selected project IDs
    roadmap_rows = db.execute(
        select(RoadmapTask.project_id, func.count(RoadmapTask.id))
        .where(RoadmapTask.project_id.in_(project_ids))
        .group_by(RoadmapTask.project_id)
    ).all()
    roadmap_by_project = {pid: (count > 0) for pid, count in roadmap_rows}

    results = [
        _build_project_response(
            p,
            bp_by_project.get(p.id, {}),
            roadmap_by_project.get(p.id, False),
        )
        for p in projects
    ]
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
