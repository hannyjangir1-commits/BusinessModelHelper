"""Pydantic v2 schemas for Execution Roadmap."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RoadmapTaskCreateRequest(BaseModel):
    """Payload to add a new task manually."""

    task_key: Optional[str] = Field(default=None, description="Identifier (e.g. TSK-10). Auto-generated if omitted.")
    milestone: str = Field(default="30-day", description="Milestone phase: 30-day, 60-day, 90-day")
    stage: str = Field(default="Research & Validation", description="Stage category")
    title: str = Field(..., min_length=3, description="Concise task title")
    description: str = Field(..., min_length=5, description="Clear description of work to execute")
    priority: str = Field(default="medium", description="low, medium, high, critical")
    status: str = Field(default="not_started", description="not_started, in_progress, completed, blocked")
    estimated_effort_days: float = Field(default=2.0, ge=0.1, le=90.0)
    start_day: int = Field(default=1, ge=1, le=365)
    duration_days: int = Field(default=7, ge=1, le=90)
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite task_keys")
    deliverable: Optional[str] = Field(default=None, description="Tangible output of this task")
    success_criteria: Optional[str] = Field(default=None, description="Definition of done")
    related_risk: Optional[str] = Field(default=None, description="Associated business or validation risk")
    kpi: Optional[str] = Field(default=None, description="Metric influenced")
    order_index: int = Field(default=0)


class RoadmapTaskUpdateRequest(BaseModel):
    """Payload to update an existing roadmap task."""

    title: Optional[str] = None
    description: Optional[str] = None
    milestone: Optional[str] = None
    stage: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimated_effort_days: Optional[float] = None
    start_day: Optional[int] = None
    duration_days: Optional[int] = None
    dependencies: Optional[List[str]] = None
    deliverable: Optional[str] = None
    success_criteria: Optional[str] = None
    related_risk: Optional[str] = None
    kpi: Optional[str] = None
    order_index: Optional[int] = None


class RoadmapTaskResponse(BaseModel):
    """Task item response."""

    id: str
    project_id: str
    task_key: str
    milestone: str
    stage: str
    title: str
    description: str
    priority: str
    status: str
    estimated_effort_days: float
    start_day: int
    duration_days: int
    dependencies: List[str]
    deliverable: Optional[str] = None
    success_criteria: Optional[str] = None
    related_risk: Optional[str] = None
    kpi: Optional[str] = None
    order_index: int
    created_at: datetime
    updated_at: datetime


class MilestoneProgress(BaseModel):
    """Progress status for a milestone phase."""

    milestone: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    completion_percentage: float


class RoadmapOverviewResponse(BaseModel):
    """Full project roadmap overview with progress indicators and tasks."""

    project_id: str
    version: int = 1
    total_tasks: int
    completed_tasks: int
    overall_completion_percentage: float
    milestones: List[MilestoneProgress]
    tasks: List[RoadmapTaskResponse]


class GeneratedTaskItem(BaseModel):
    """Schema for individual task during AI generation."""

    task_key: str
    milestone: str
    stage: str
    title: str
    description: str
    priority: str = "medium"
    estimated_effort_days: float = 2.0
    start_day: int = 1
    duration_days: int = 7
    dependencies: List[str] = Field(default_factory=list)
    deliverable: Optional[str] = None
    success_criteria: Optional[str] = None
    related_risk: Optional[str] = None
    kpi: Optional[str] = None


class GeneratedRoadmapData(BaseModel):
    """AI structured output containing recommended tasks."""

    roadmap_philosophy: str
    tasks: List[GeneratedTaskItem]
