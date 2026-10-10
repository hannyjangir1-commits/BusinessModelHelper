"""Technology Stack Recommendation Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TechRecommendationItem(BaseModel):
    """Specific architectural component recommendation."""
    category: str = Field(..., description="Category: Frontend, Backend, Database, Hosting & Infrastructure, Third-Party Services")
    technology: str = Field(..., min_length=2, description="Specific technology, framework, or provider")
    purpose: str = Field(..., min_length=5, description="Role of this component in the application")
    reason: str = Field(..., min_length=10, description="Why this fits team, budget, stage, and constraints")
    alternatives: List[str] = Field(default_factory=list, description="Viable alternative technologies considered")
    tradeoffs: List[str] = Field(default_factory=list, description="Trade-offs, complexity, or developer experience drawbacks")
    estimated_cost: str = Field(..., description="Estimated cost tier or range (e.g. Free Tier, $5-$20/mo)")
    cost_period: str = Field(default="monthly", description="Billing frequency: monthly, annual, usage-based, free")
    cost_assumptions: List[str] = Field(default_factory=list, description="Traffic, storage, or volume assumptions for this cost")
    constraints: List[str] = Field(default_factory=list, description="Key operational or ecosystem constraints")
    verification_notes: str = Field(..., description="Notice that pricing is an estimate requiring live verification")

    @field_validator("alternatives", "tradeoffs", "cost_assumptions", "constraints", mode="before")
    @classmethod
    def ensure_list_of_strings(cls, v):
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class TechnologyStackData(BaseModel):
    """Complete multi-category Technology Stack recommendation."""
    architecture_summary: str = Field(..., min_length=20, description="High-level architectural philosophy and rationale")
    estimated_monthly_infrastructure_total: str = Field(..., description="Estimated total monthly spend for initial launch")

    frontend: TechRecommendationItem = Field(..., description="Frontend architecture recommendation")
    backend: TechRecommendationItem = Field(..., description="Backend architecture recommendation")
    database: TechRecommendationItem = Field(..., description="Database architecture recommendation")
    hosting_infrastructure: TechRecommendationItem = Field(..., description="Hosting and deployment platform recommendation")
    third_party_services: TechRecommendationItem = Field(..., description="Essential APIs, auth, email, or monitoring recommendations")

    scalability_considerations: List[str] = Field(default_factory=list, description="How the stack evolves from 0 to 100k users")
    security_considerations: List[str] = Field(default_factory=list, description="Key security measures, secrets handling, and compliance")

    @field_validator("scalability_considerations", "security_considerations", mode="before")
    @classmethod
    def ensure_list_of_strings(cls, v):
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class TechStackUpdateRequest(BaseModel):
    """Schema for editing saved technology stack recommendations."""
    content: TechnologyStackData
