"""Execution Roadmap service, DAG cycle validation, and persistent task CRUD."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import asc, desc, func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.blueprint import Blueprint
from app.models.generation import GenerationRun
from app.models.project import Project
from app.models.roadmap_task import RoadmapTask
from app.models.user import User
from app.schemas.roadmap import (
    GeneratedRoadmapData,
    MilestoneProgress,
    RoadmapOverviewResponse,
    RoadmapTaskCreateRequest,
    RoadmapTaskResponse,
    RoadmapTaskUpdateRequest,
)
from app.services.ai.client import GeminiAIClient
from app.services.ai.prompts import PROMPT_VERSION
from app.services.project_service import get_user_project_by_id

logger = logging.getLogger(__name__)


def validate_dag_dependencies(tasks: List[Dict[str, Any]]) -> None:
    """Ensure task dependencies do not contain circular references (DAG cycle check via DFS)."""
    graph: Dict[str, List[str]] = {}
    all_keys: Set[str] = set()

    for t in tasks:
        key = t.get("task_key", "")
        all_keys.add(key)
        graph[key] = t.get("dependencies", [])

    # Verify all referenced dependency keys exist in the task set
    for key, deps in graph.items():
        for dep in deps:
            if dep not in all_keys and dep != key:
                # Remove stale or invalid dependency references silently to preserve stability
                graph[key] = [d for d in deps if d in all_keys and d != key]

    # Cycle detection using 3-color DFS
    # 0 = unvisited, 1 = visiting (in current recursion stack), 2 = visited
    visited: Dict[str, int] = {k: 0 for k in all_keys}

    def dfs(node: str) -> bool:
        visited[node] = 1
        for neighbor in graph.get(node, []):
            if neighbor == node:
                return True  # Self-dependency
            if visited.get(neighbor) == 1:
                return True  # Back-edge detected (Cycle!)
            if visited.get(neighbor) == 0:
                if dfs(neighbor):
                    return True
        visited[node] = 2
        return False

    for node in all_keys:
        if visited[node] == 0:
            if dfs(node):
                raise ValidationError(f"Circular dependency detected in roadmap tasks involving task '{node}'.")


def build_roadmap_prompt(project: Project) -> Tuple[str, str]:
    """Construct prompt for execution roadmap generation."""
    system_instruction = (
        "You are an Agile Technical Project Manager and Startup Operations Architect. "
        "Create an actionable, sequential 30-day, 60-day, and 90-day execution roadmap "
        "for the founder's business idea. "
        "Tasks must have realistic timeframes and logical prerequisite dependencies. "
        "Dependencies must form a Directed Acyclic Graph with NO circular dependencies. "
        "Prioritize de-risking the largest assumptions in the first 30 days before heavy technical buildout. "
        "Return ONLY a single valid JSON object adhering to the schema without markdown."
    )

    user_prompt = f"""
Business Context:
Project Name: {project.name}
Industry: {project.industry}
Idea: {project.idea_description}
Business Stage: {project.business_stage}
Budget: {project.budget_amount or 'Bootstrapped'} {project.budget_currency}
Team Size: {project.team_size or 'Solo Founder'}

Generate a structured execution plan with 8 to 12 core tasks divided across '30-day', '60-day', and '90-day' milestones:
{{
  "roadmap_philosophy": "<Core execution strategy and sequencing rationale>",
  "tasks": [
    {{
      "task_key": "TSK-01",
      "milestone": "30-day",
      "stage": "Research & Validation",
      "title": "<High priority validation task>",
      "description": "<Detailed procedure>",
      "priority": "critical",
      "estimated_effort_days": 3.0,
      "start_day": 1,
      "duration_days": 7,
      "dependencies": [],
      "deliverable": "<Specific document or data>",
      "success_criteria": "<Pass threshold>",
      "related_risk": "<Associated risk>",
      "kpi": "<KPI tracked>"
    }},
    {{
      "task_key": "TSK-02",
      "milestone": "30-day",
      "stage": "Planning",
      "title": "<System architecture & wireframes>",
      "description": "<Design MVP scope and API contracts>",
      "priority": "high",
      "estimated_effort_days": 4.0,
      "start_day": 8,
      "duration_days": 7,
      "dependencies": ["TSK-01"],
      "deliverable": "<Interactive wireframes and API schema>",
      "success_criteria": "<Core user flows signed off>",
      "related_risk": "Feature creep",
      "kpi": "MVP feature count <= 5"
    }},
    {{
      "task_key": "TSK-03",
      "milestone": "60-day",
      "stage": "Prototype or MVP",
      "title": "<MVP Implementation>",
      "description": "<Build core backend and reactive frontend>",
      "priority": "critical",
      "estimated_effort_days": 12.0,
      "start_day": 15,
      "duration_days": 21,
      "dependencies": ["TSK-02"],
      "deliverable": "<Functional containerized web app>",
      "success_criteria": "<Automated test suite passing and deployed on Render>",
      "related_risk": "Technical delay",
      "kpi": "Lighthouse score >= 90"
    }},
    {{
      "task_key": "TSK-04",
      "milestone": "90-day",
      "stage": "Initial Customer Acquisition",
      "title": "<Beta Cohort Onboarding & Feedback>",
      "description": "<Recruit 10 beta testers and measure core workflow completion>",
      "priority": "high",
      "estimated_effort_days": 5.0,
      "start_day": 45,
      "duration_days": 14,
      "dependencies": ["TSK-03"],
      "deliverable": "<Cohort feedback log>",
      "success_criteria": ">= 60% activation rate",
      "related_risk": "Customer friction",
      "kpi": "NPS >= 40"
    }}
  ]
}}
"""
    return system_instruction, user_prompt


def validate_roadmap_response(raw_text: str) -> GeneratedRoadmapData:
    """Parse JSON and validate against GeneratedRoadmapData schema."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data_dict = json.loads(cleaned)
    except Exception as e:
        raise ValidationError(f"AI returned invalid JSON: {str(e)}")

    try:
        validated = GeneratedRoadmapData.model_validate(data_dict)
    except Exception as e:
        raise ValidationError(f"Roadmap failed schema validation: {str(e)}")

    # Check for DAG cycles
    tasks_dicts = [t.model_dump() for t in validated.tasks]
    validate_dag_dependencies(tasks_dicts)

    return validated


def generate_execution_roadmap(
    db: Session,
    user: User,
    project: Project,
    client: Optional[Any] = None,
) -> Tuple[Blueprint, List[str]]:
    """Generate roadmap tasks via AI, validate DAG, clear old tasks, and persist both rows and blueprint snapshot."""
    ai_client = client or GeminiAIClient()
    model_name = getattr(ai_client, "model", "gemini-2.5-flash")

    # 1. Audit generation run record
    run = GenerationRun(
        project_id=project.id,
        user_id=user.id,
        module_type="execution_roadmap",
        status="running",
        model=model_name,
        prompt_version=PROMPT_VERSION,
    )
    db.add(run)
    db.commit()
    run_id = run.id

    try:
        system_instruction, user_prompt = build_roadmap_prompt(project)
        raw_text, latency_ms, input_tokens, output_tokens = ai_client.generate(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        validated_data = validate_roadmap_response(raw_text)

        # 2. Increment version and save blueprint snapshot
        latest_version = db.execute(
            select(func.coalesce(func.max(Blueprint.version), 0)).where(
                Blueprint.project_id == project.id,
                Blueprint.module_type == "execution_roadmap",
            )
        ).scalar_one()
        new_version = latest_version + 1

        blueprint = Blueprint(
            project_id=project.id,
            module_type="execution_roadmap",
            version=new_version,
            content_json=validated_data.model_dump(),
        )
        db.add(blueprint)

        # 3. Replace current roadmap_tasks with new generated tasks
        db.query(RoadmapTask).filter(RoadmapTask.project_id == project.id).delete()

        for idx, task_item in enumerate(validated_data.tasks):
            db_task = RoadmapTask(
                project_id=project.id,
                user_id=user.id,
                task_key=task_item.task_key,
                milestone=task_item.milestone,
                stage=task_item.stage,
                title=task_item.title,
                description=task_item.description,
                priority=task_item.priority,
                status="not_started",
                estimated_effort_days=task_item.estimated_effort_days,
                start_day=task_item.start_day,
                duration_days=task_item.duration_days,
                dependencies_json=task_item.dependencies,
                deliverable=task_item.deliverable,
                success_criteria=task_item.success_criteria,
                related_risk=task_item.related_risk,
                kpi=task_item.kpi,
                order_index=idx,
            )
            db.add(db_task)

        # 4. Complete audit run
        db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(
                status="success",
                latency_ms=latency_ms,
                input_token_count=input_tokens,
                output_token_count=output_tokens,
                completed_at=datetime.now(timezone.utc),
            )
        )

        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(blueprint)
        return blueprint, []

    except Exception as e:
        db.rollback()
        error_code = getattr(e, "code", "ROADMAP_GENERATION_FAILED")
        error_msg = getattr(e, "message", str(e))

        db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(
                status="failed",
                error_code=error_code,
                error_message=error_msg,
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        logger.error(f"Roadmap generation failed: {error_msg}")
        raise


def get_project_roadmap_overview(
    db: Session,
    user: User,
    project_id: str,
) -> RoadmapOverviewResponse:
    """Retrieve all persisted roadmap tasks and compute milestone progress percentages."""
    get_user_project_by_id(db, user, project_id)

    tasks = (
        db.query(RoadmapTask)
        .filter(RoadmapTask.project_id == project_id)
        .order_by(asc(RoadmapTask.start_day), asc(RoadmapTask.order_index))
        .all()
    )

    task_responses: List[RoadmapTaskResponse] = []
    total_tasks = len(tasks)
    completed_count = 0

    milestone_stats: Dict[str, Dict[str, int]] = {
        "30-day": {"total": 0, "completed": 0, "in_progress": 0},
        "60-day": {"total": 0, "completed": 0, "in_progress": 0},
        "90-day": {"total": 0, "completed": 0, "in_progress": 0},
    }

    for t in tasks:
        resp = RoadmapTaskResponse(
            id=t.id,
            project_id=t.project_id,
            task_key=t.task_key,
            milestone=t.milestone,
            stage=t.stage,
            title=t.title,
            description=t.description,
            priority=t.priority,
            status=t.status,
            estimated_effort_days=t.estimated_effort_days,
            start_day=t.start_day,
            duration_days=t.duration_days,
            dependencies=t.dependencies_json or [],
            deliverable=t.deliverable,
            success_criteria=t.success_criteria,
            related_risk=t.related_risk,
            kpi=t.kpi,
            order_index=t.order_index,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        task_responses.append(resp)

        ms = t.milestone if t.milestone in milestone_stats else "30-day"
        milestone_stats[ms]["total"] += 1

        if t.status == "completed":
            completed_count += 1
            milestone_stats[ms]["completed"] += 1
        elif t.status == "in_progress":
            milestone_stats[ms]["in_progress"] += 1

    overall_pct = round((completed_count / total_tasks * 100.0), 1) if total_tasks > 0 else 0.0

    milestones_progress = [
        MilestoneProgress(
            milestone=ms_name,
            total_tasks=data["total"],
            completed_tasks=data["completed"],
            in_progress_tasks=data["in_progress"],
            completion_percentage=round((data["completed"] / data["total"] * 100.0), 1) if data["total"] > 0 else 0.0,
        )
        for ms_name, data in milestone_stats.items()
    ]

    # Latest version
    latest_version = db.execute(
        select(func.coalesce(func.max(Blueprint.version), 1)).where(
            Blueprint.project_id == project_id,
            Blueprint.module_type == "execution_roadmap",
        )
    ).scalar_one()

    return RoadmapOverviewResponse(
        project_id=project_id,
        version=latest_version,
        total_tasks=total_tasks,
        completed_tasks=completed_count,
        overall_completion_percentage=overall_pct,
        milestones=milestones_progress,
        tasks=task_responses,
    )


def create_roadmap_task(
    db: Session,
    user: User,
    project_id: str,
    req: RoadmapTaskCreateRequest,
) -> RoadmapTaskResponse:
    """Manually add a task to the project's execution roadmap."""
    project = get_user_project_by_id(db, user, project_id)

    task_key = req.task_key
    if not task_key:
        count = db.query(RoadmapTask).filter(RoadmapTask.project_id == project.id).count()
        task_key = f"TSK-{count + 1:02d}"

    task = RoadmapTask(
        project_id=project.id,
        user_id=user.id,
        task_key=task_key,
        milestone=req.milestone,
        stage=req.stage,
        title=req.title,
        description=req.description,
        priority=req.priority,
        status=req.status,
        estimated_effort_days=req.estimated_effort_days,
        start_day=req.start_day,
        duration_days=req.duration_days,
        dependencies_json=req.dependencies,
        deliverable=req.deliverable,
        success_criteria=req.success_criteria,
        related_risk=req.related_risk,
        kpi=req.kpi,
        order_index=req.order_index,
    )
    db.add(task)
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    return RoadmapTaskResponse(
        id=task.id,
        project_id=task.project_id,
        task_key=task.task_key,
        milestone=task.milestone,
        stage=task.stage,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        estimated_effort_days=task.estimated_effort_days,
        start_day=task.start_day,
        duration_days=task.duration_days,
        dependencies=task.dependencies_json or [],
        deliverable=task.deliverable,
        success_criteria=task.success_criteria,
        related_risk=task.related_risk,
        kpi=task.kpi,
        order_index=task.order_index,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def update_roadmap_task(
    db: Session,
    user: User,
    project_id: str,
    task_id: str,
    req: RoadmapTaskUpdateRequest,
) -> RoadmapTaskResponse:
    """Update task status, priority, or details."""
    get_user_project_by_id(db, user, project_id)

    task = (
        db.query(RoadmapTask)
        .filter(RoadmapTask.id == task_id, RoadmapTask.project_id == project_id)
        .first()
    )
    if not task:
        raise NotFoundError("Roadmap task not found.")

    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.milestone is not None:
        task.milestone = req.milestone
    if req.stage is not None:
        task.stage = req.stage
    if req.priority is not None:
        task.priority = req.priority
    if req.status is not None:
        task.status = req.status
    if req.estimated_effort_days is not None:
        task.estimated_effort_days = req.estimated_effort_days
    if req.start_day is not None:
        task.start_day = req.start_day
    if req.duration_days is not None:
        task.duration_days = req.duration_days
    if req.dependencies is not None:
        task.dependencies_json = req.dependencies
    if req.deliverable is not None:
        task.deliverable = req.deliverable
    if req.success_criteria is not None:
        task.success_criteria = req.success_criteria
    if req.related_risk is not None:
        task.related_risk = req.related_risk
    if req.kpi is not None:
        task.kpi = req.kpi
    if req.order_index is not None:
        task.order_index = req.order_index

    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    return RoadmapTaskResponse(
        id=task.id,
        project_id=task.project_id,
        task_key=task.task_key,
        milestone=task.milestone,
        stage=task.stage,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        estimated_effort_days=task.estimated_effort_days,
        start_day=task.start_day,
        duration_days=task.duration_days,
        dependencies=task.dependencies_json or [],
        deliverable=task.deliverable,
        success_criteria=task.success_criteria,
        related_risk=task.related_risk,
        kpi=task.kpi,
        order_index=task.order_index,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def delete_roadmap_task(
    db: Session,
    user: User,
    project_id: str,
    task_id: str,
) -> None:
    """Delete a specific roadmap task."""
    get_user_project_by_id(db, user, project_id)

    task = (
        db.query(RoadmapTask)
        .filter(RoadmapTask.id == task_id, RoadmapTask.project_id == project_id)
        .first()
    )
    if not task:
        raise NotFoundError("Roadmap task not found.")

    db.delete(task)
    db.commit()
