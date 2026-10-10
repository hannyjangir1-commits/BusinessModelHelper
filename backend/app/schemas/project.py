"""Project request and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Project name")
    idea_description: str = Field(..., min_length=10, max_length=5000, description="Detailed business idea description")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry or business sector")
    business_stage: str = Field(default="idea", description="Current stage: idea, validation, prototype, mvp, growth")
    target_market: Optional[str] = Field(None, max_length=150, description="Geographic or market segment")
    target_audience: Optional[str] = Field(None, max_length=1000, description="Target customer profile")

    budget_amount: Optional[float] = Field(None, ge=0, description="Estimated capital / budget")
    budget_currency: str = Field(default="USD", min_length=3, max_length=10)
    team_size: Optional[str] = Field(None, max_length=50, description="e.g. Solo, 2-5, 5-10, 10+")
    technical_preferences: Optional[str] = Field(None, max_length=1000, description="Preferred stacks or tools")
    constraints: Optional[str] = Field(None, max_length=1000, description="Regulatory, time, or cost constraints")

    @field_validator("name", "industry")
    @classmethod
    def clean_str(cls, v: str) -> str:
        return v.strip()


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    idea_description: Optional[str] = Field(None, min_length=10, max_length=5000)
    industry: Optional[str] = Field(None, min_length=2, max_length=100)
    business_stage: Optional[str] = None
    target_market: Optional[str] = None
    target_audience: Optional[str] = None
    budget_amount: Optional[float] = Field(None, ge=0)
    budget_currency: Optional[str] = None
    team_size: Optional[str] = None
    technical_preferences: Optional[str] = None
    constraints: Optional[str] = None


class BlueprintSummary(BaseModel):
    id: str
    module_type: str
    version: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    idea_description: str
    industry: str
    business_stage: str
    target_market: Optional[str] = None
    target_audience: Optional[str] = None
    budget_amount: Optional[float] = None
    budget_currency: str = "USD"
    team_size: Optional[str] = None
    technical_preferences: Optional[str] = None
    constraints: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    has_business_model: bool = False
    has_technology_stack: bool = False
    latest_bmc_version: Optional[int] = None
    latest_tech_version: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
