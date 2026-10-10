"""Pydantic v2 schemas for Business Blueprint Copilot."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    """Payload to interact with the project copilot."""

    query: str = Field(..., min_length=3, description="User question or edit instruction")
    action_type: str = Field(
        default="answer_question",
        description="Explicit intent: 'answer_question' (Q&A advisory) or 'propose_edit' (structured section edit)",
    )
    target_module: Optional[str] = Field(
        default=None,
        description="Target module if proposing edit: business_model, technology_stack, validation_report, financial_model, execution_roadmap",
    )
    target_section: Optional[str] = Field(
        default=None,
        description="Specific block/section key (e.g. customer_segments, revenue_streams, frontend)",
    )


class CopilotProposalResponse(BaseModel):
    """Structured proposal representing a proposed modification to saved project blueprints."""

    proposal_id: str
    target_module: str
    target_section: str
    previous_content: Optional[Any] = None
    proposed_content: Any
    reasoning: Optional[str] = None
    status: str = "pending"  # pending, accepted, rejected
    created_at: datetime


class CopilotChatResponse(BaseModel):
    """Unified response for copilot interactions."""

    action_type: str
    answer: Optional[str] = None
    proposal: Optional[CopilotProposalResponse] = None


class CopilotRevisionItem(BaseModel):
    """Historical audit record of a proposal."""

    id: str
    target_module: str
    target_section: str
    action_type: str
    status: str
    user_query: str
    reasoning: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class ProposedEditStructuredOutput(BaseModel):
    """Strict schema for AI structured proposed edits."""

    target_module: str
    target_section: str
    reasoning: str
    proposed_content: Dict[str, Any]
