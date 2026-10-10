"""Business Blueprint Copilot API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotProposalResponse,
    CopilotRevisionItem,
)
from app.services.copilot_service import (
    accept_copilot_proposal,
    list_project_copilot_revisions,
    process_copilot_interaction,
    reject_copilot_proposal,
)

router = APIRouter(prefix="/projects/{project_id}/copilot", tags=["Blueprint Copilot"])


@router.post("/chat", response_model=ApiResponse[CopilotChatResponse])
def copilot_chat(
    project_id: str,
    req: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[CopilotChatResponse]:
    """Interact with Business Blueprint Copilot (ask strategic questions or propose section edits)."""
    response = process_copilot_interaction(db, current_user, project_id, req)
    return ApiResponse(data=response)


@router.post("/proposals/{proposal_id}/accept", response_model=ApiResponse[CopilotProposalResponse])
def accept_proposal(
    project_id: str,
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[CopilotProposalResponse]:
    """Explicitly accept and apply a proposed section edit to the underlying blueprint."""
    resolved = accept_copilot_proposal(db, current_user, project_id, proposal_id)
    return ApiResponse(data=resolved, message="Proposal accepted and applied to blueprint successfully.")


@router.post("/proposals/{proposal_id}/reject", response_model=ApiResponse[CopilotProposalResponse])
def reject_proposal(
    project_id: str,
    proposal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[CopilotProposalResponse]:
    """Explicitly reject a proposed section edit (underlying blueprints remain unchanged)."""
    resolved = reject_copilot_proposal(db, current_user, project_id, proposal_id)
    return ApiResponse(data=resolved, message="Proposal rejected. No changes made to blueprint.")


@router.get("/revisions", response_model=ApiResponse[List[CopilotRevisionItem]])
@router.get("/proposals", response_model=ApiResponse[List[CopilotRevisionItem]])
def list_revisions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[CopilotRevisionItem]]:
    """List historical copilot edit proposals and decisions for this project."""
    revisions = list_project_copilot_revisions(db, current_user, project_id)
    return ApiResponse(data=revisions)
