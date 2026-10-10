"""Business Model Canvas Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class BMCBlock(BaseModel):
    """Schema for each of the nine Business Model Canvas blocks."""
    block_title: str = Field(..., description="Standard title of the canvas block")
    summary: str = Field(..., min_length=10, description="Concise strategic summary")
    recommendations: List[str] = Field(..., min_length=1, description="Actionable recommendations")
    rationale: str = Field(..., min_length=10, description="Why this recommendation fits the business")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions requiring market validation")
    risks_uncertainties: List[str] = Field(default_factory=list, description="Potential risks or unknowns")
    validation_experiments: List[str] = Field(default_factory=list, description="Suggested experiments to test assumptions")

    @field_validator("recommendations", "assumptions", "risks_uncertainties", "validation_experiments", mode="before")
    @classmethod
    def ensure_list_of_strings(cls, v):
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(x) for x in v]
        return []


class BusinessModelCanvasData(BaseModel):
    """Complete 9-block Business Model Canvas structured output."""
    overview: str = Field(..., min_length=20, description="Executive overview of the business model")
    key_strategic_focus: str = Field(..., min_length=10, description="Primary competitive advantage or core strategy")

    customer_segments: BMCBlock = Field(..., description="1. Customer Segments")
    value_propositions: BMCBlock = Field(..., description="2. Value Propositions")
    channels: BMCBlock = Field(..., description="3. Channels")
    customer_relationships: BMCBlock = Field(..., description="4. Customer Relationships")
    revenue_streams: BMCBlock = Field(..., description="5. Revenue Streams")
    key_resources: BMCBlock = Field(..., description="6. Key Resources")
    key_activities: BMCBlock = Field(..., description="7. Key Activities")
    key_partnerships: BMCBlock = Field(..., description="8. Key Partnerships")
    cost_structure: BMCBlock = Field(..., description="9. Cost Structure")


class BMCUpdateRequest(BaseModel):
    """Schema for editing individual blocks or entire canvas."""
    content: BusinessModelCanvasData
