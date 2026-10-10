"""Business Blueprint Copilot service for grounded Q&A and controlled section editing."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.blueprint import Blueprint
from app.models.copilot_revision import CopilotRevision
from app.models.financial_model import FinancialModel
from app.models.project import Project
from app.models.roadmap_task import RoadmapTask
from app.models.user import User
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotProposalResponse,
    CopilotRevisionItem,
    ProposedEditStructuredOutput,
)
from app.services.ai.client import GeminiAIClient
from app.services.project_service import get_user_project_by_id

logger = logging.getLogger(__name__)


def build_copilot_context_summary(db: Session, project: Project) -> str:
    """Aggregate sanitized summaries of all saved project modules."""
    lines = [
        f"Project Name: {project.name}",
        f"Industry: {project.industry}",
        f"Business Idea: {project.idea_description}",
        f"Business Stage: {project.business_stage}",
        f"Target Market: {project.target_market or 'General'}",
        f"Budget: {project.budget_amount or 'Bootstrapped'} {project.budget_currency}",
    ]

    # BMC Summary
    bmc = (
        db.query(Blueprint)
        .filter(Blueprint.project_id == project.id, Blueprint.module_type == "business_model")
        .order_by(Blueprint.version.desc())
        .first()
    )
    if bmc and bmc.content_json:
        lines.append(f"Business Model Canvas (v{bmc.version}): Available")
        lines.append(f"  Overview: {bmc.content_json.get('overview', '')}")
        lines.append(f"  Strategic Focus: {bmc.content_json.get('key_strategic_focus', '')}")

    # Tech Stack Summary
    tech = (
        db.query(Blueprint)
        .filter(Blueprint.project_id == project.id, Blueprint.module_type == "technology_stack")
        .order_by(Blueprint.version.desc())
        .first()
    )
    if tech and tech.content_json:
        lines.append(f"Technology Stack (v{tech.version}): Available")
        lines.append(f"  Architecture Philosophy: {tech.content_json.get('architecture_summary', '')}")
        lines.append(f"  Estimated Monthly Launch Cost: {tech.content_json.get('estimated_monthly_infrastructure_total', '')}")

    # Financial Summary
    fin = (
        db.query(FinancialModel)
        .filter(FinancialModel.project_id == project.id)
        .order_by(FinancialModel.version.desc())
        .first()
    )
    if fin and fin.projections_json:
        sum_data = fin.projections_json.get("summary", {})
        be_data = fin.projections_json.get("break_even", {})
        lines.append(f"Financial Model (v{fin.version}): Available")
        lines.append(f"  Total Revenue: {sum_data.get('total_revenue', '')}")
        lines.append(f"  Ending Cash: {sum_data.get('ending_cash_balance', '')}")
        lines.append(f"  Runway: {sum_data.get('estimated_runway_months', 'Profitable')}")
        lines.append(f"  Break-Even Units/Month: {be_data.get('break_even_units_per_month', 'N/A')}")

    # Roadmap Summary
    task_count = db.query(RoadmapTask).filter(RoadmapTask.project_id == project.id).count()
    if task_count > 0:
        lines.append(f"Execution Roadmap: {task_count} active tasks configured")

    return "\n".join(lines)


def process_copilot_interaction(
    db: Session,
    user: User,
    project_id: str,
    req: CopilotChatRequest,
    client: Optional[Any] = None,
) -> CopilotChatResponse:
    """Orchestrate copilot interaction: routes between read-only Q&A advisory and controlled propose_edit."""
    project = get_user_project_by_id(db, user, project_id)
    ai_client = client or GeminiAIClient()
    context_str = build_copilot_context_summary(db, project)

    # 1. READ-ONLY Q&A ADVISORY (Zero data modifications)
    if req.action_type == "answer_question":
        system_instruction = (
            "You are an expert AI Business Architect Copilot and startup strategy partner. "
            "Answer the founder's question using the provided saved project context. "
            "Be concise, actionable, and direct. "
            "Ground your answer strictly in the provided project context without fabricating details. "
            "If asked for opinions or comparisons, provide balanced trade-offs. "
            "Do NOT propose or execute database updates in Q&A mode."
        )
        user_prompt = f"""
Saved Project Context:
{context_str}

Founder Question:
{req.query}
"""
        raw_text, _, _, _ = ai_client.generate(system_instruction, user_prompt)
        return CopilotChatResponse(
            action_type="answer_question",
            answer=raw_text.strip(),
        )

    # 2. CONTROLLED PROPOSE_EDIT
    elif req.action_type == "propose_edit":
        target_mod = req.target_module or "business_model"
        target_sec = req.target_section or "customer_segments"

        # Load current content for target module and section
        previous_content: Optional[Any] = None
        if target_mod == "business_model":
            bmc = (
                db.query(Blueprint)
                .filter(Blueprint.project_id == project.id, Blueprint.module_type == "business_model")
                .order_by(Blueprint.version.desc())
                .first()
            )
            if bmc and bmc.content_json:
                previous_content = bmc.content_json.get(target_sec, {})
        elif target_mod == "technology_stack":
            tech = (
                db.query(Blueprint)
                .filter(Blueprint.project_id == project.id, Blueprint.module_type == "technology_stack")
                .order_by(Blueprint.version.desc())
                .first()
            )
            if tech and tech.content_json:
                previous_content = tech.content_json.get(target_sec, {})
        elif target_mod == "financial_model":
            fin = (
                db.query(FinancialModel)
                .filter(FinancialModel.project_id == project.id)
                .order_by(FinancialModel.version.desc())
                .first()
            )
            if fin:
                previous_content = fin.assumptions_json

        system_instruction = (
            "You are a strict, structured AI Code & Business Blueprint Editor. "
            "The user wishes to modify a specific section of their business blueprint. "
            "Analyze their request, review the current content, and generate a structured replacement. "
            "Return ONLY a single valid JSON object matching this schema: "
            "{\n"
            '  "target_module": "<module_name>",\n'
            '  "target_section": "<section_name>",\n'
            '  "reasoning": "<clear explanation of what was changed and why>",\n'
            '  "proposed_content": { ... updated fields for this section ... }\n'
            "}\n"
            "Do NOT include markdown formatting or extra prose."
        )

        user_prompt = f"""
Project Context:
{context_str}

Target Module: {target_mod}
Target Section: {target_sec}
Current Content: {json.dumps(previous_content) if previous_content else 'None'}

Founder Edit Instruction:
{req.query}
"""
        raw_text, _, _, _ = ai_client.generate(system_instruction, user_prompt)

        # Parse proposed edit JSON
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed_proposal = json.loads(cleaned)
            reasoning = parsed_proposal.get("reasoning", "Proposed refinement based on founder prompt.")
            proposed_content = parsed_proposal.get("proposed_content", parsed_proposal)
        except Exception:
            reasoning = "Proposed refinement based on founder prompt."
            proposed_content = {"summary": cleaned}

        # Persist pending CopilotRevision record
        revision = CopilotRevision(
            project_id=project.id,
            user_id=user.id,
            target_module=target_mod,
            target_section=target_sec,
            action_type="propose_edit",
            status="pending",
            user_query=req.query,
            proposal_content=proposed_content,
            previous_content=previous_content if isinstance(previous_content, dict) else None,
            reasoning=reasoning,
            model=getattr(ai_client, "model", "gemini-2.5-flash"),
        )
        db.add(revision)
        db.commit()
        db.refresh(revision)

        return CopilotChatResponse(
            action_type="propose_edit",
            proposal=CopilotProposalResponse(
                proposal_id=revision.id,
                target_module=revision.target_module,
                target_section=revision.target_section,
                previous_content=revision.previous_content,
                proposed_content=revision.proposal_content,
                reasoning=revision.reasoning,
                status=revision.status,
                created_at=revision.created_at,
            ),
        )

    else:
        raise ValidationError(f"Invalid action_type '{req.action_type}'. Must be 'answer_question' or 'propose_edit'.")


def accept_copilot_proposal(
    db: Session,
    user: User,
    project_id: str,
    proposal_id: str,
) -> CopilotProposalResponse:
    """Apply an accepted proposal to the underlying persistent module."""
    get_user_project_by_id(db, user, project_id)

    rev = (
        db.query(CopilotRevision)
        .filter(CopilotRevision.id == proposal_id, CopilotRevision.project_id == project_id)
        .first()
    )
    if not rev:
        raise NotFoundError("Copilot proposal not found.")

    if rev.status != "pending":
        raise ConflictError(f"Proposal has already been resolved with status '{rev.status}'.")

    # Apply edit to target module
    if rev.target_module == "business_model":
        bmc = (
            db.query(Blueprint)
            .filter(Blueprint.project_id == project_id, Blueprint.module_type == "business_model")
            .order_by(Blueprint.version.desc())
            .first()
        )
        if bmc and isinstance(bmc.content_json, dict):
            updated_json = dict(bmc.content_json)
            updated_json[rev.target_section] = rev.proposal_content
            bmc.content_json = updated_json
            bmc.updated_at = datetime.now(timezone.utc)

    elif rev.target_module == "technology_stack":
        tech = (
            db.query(Blueprint)
            .filter(Blueprint.project_id == project_id, Blueprint.module_type == "technology_stack")
            .order_by(Blueprint.version.desc())
            .first()
        )
        if tech and isinstance(tech.content_json, dict):
            updated_json = dict(tech.content_json)
            updated_json[rev.target_section] = rev.proposal_content
            tech.content_json = updated_json
            tech.updated_at = datetime.now(timezone.utc)

    elif rev.target_module == "financial_model":
        fin = (
            db.query(FinancialModel)
            .filter(FinancialModel.project_id == project_id)
            .order_by(FinancialModel.version.desc())
            .first()
        )
        if fin and isinstance(rev.proposal_content, dict):
            # Update matching assumptions
            current_assump = dict(fin.assumptions_json)
            for k, v in rev.proposal_content.items():
                if k in current_assump:
                    current_assump[k] = v
            fin.assumptions_json = current_assump
            fin.updated_at = datetime.now(timezone.utc)

    # Mark proposal accepted
    rev.status = "accepted"
    rev.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rev)

    return CopilotProposalResponse(
        proposal_id=rev.id,
        target_module=rev.target_module,
        target_section=rev.target_section,
        previous_content=rev.previous_content,
        proposed_content=rev.proposal_content,
        reasoning=rev.reasoning,
        status=rev.status,
        created_at=rev.created_at,
    )


def reject_copilot_proposal(
    db: Session,
    user: User,
    project_id: str,
    proposal_id: str,
) -> CopilotProposalResponse:
    """Explicitly reject a proposal, leaving all underlying modules unchanged."""
    get_user_project_by_id(db, user, project_id)

    rev = (
        db.query(CopilotRevision)
        .filter(CopilotRevision.id == proposal_id, CopilotRevision.project_id == project_id)
        .first()
    )
    if not rev:
        raise NotFoundError("Copilot proposal not found.")

    if rev.status != "pending":
        raise ConflictError(f"Proposal has already been resolved with status '{rev.status}'.")

    # Mark proposal rejected (zero changes to blueprints)
    rev.status = "rejected"
    rev.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rev)

    return CopilotProposalResponse(
        proposal_id=rev.id,
        target_module=rev.target_module,
        target_section=rev.target_section,
        previous_content=rev.previous_content,
        proposed_content=rev.proposal_content,
        reasoning=rev.reasoning,
        status=rev.status,
        created_at=rev.created_at,
    )


def list_project_copilot_revisions(
    db: Session,
    user: User,
    project_id: str,
) -> List[CopilotRevisionItem]:
    """Retrieve all historical copilot proposals for audit and history view."""
    get_user_project_by_id(db, user, project_id)

    revs = (
        db.query(CopilotRevision)
        .filter(CopilotRevision.project_id == project_id)
        .order_by(desc(CopilotRevision.created_at))
        .all()
    )

    return [
        CopilotRevisionItem(
            id=r.id,
            target_module=r.target_module,
            target_section=r.target_section,
            action_type=r.action_type,
            status=r.status,
            user_query=r.user_query,
            reasoning=r.reasoning,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
        )
        for r in revs
    ]
