"""Deterministic business rules and consistency checks."""

from typing import List, Tuple
from app.models.project import Project
from app.schemas.business_model import BusinessModelCanvasData
from app.schemas.technology_stack import TechnologyStackData


def evaluate_bmc_rules(canvas: BusinessModelCanvasData, project: Project) -> Tuple[BusinessModelCanvasData, List[str]]:
    """Apply deterministic validation and advisory checks to Business Model Canvas."""
    warnings: List[str] = []

    # Check budget consistency
    if project.budget_amount is not None and project.budget_amount < 1000:
        expensive_keywords = ["billboard", "tv ad", "enterprise sales team", "custom hardware", "celebrity"]
        channels_text = " ".join(canvas.channels.recommendations).lower()
        if any(kw in channels_text for kw in expensive_keywords):
            warnings.append(
                "Advisory: Proposed marketing channels may exceed the allocated budget ($"
                f"{project.budget_amount:.0f}). Prioritize organic or self-serve digital channels."
            )

    # Check key partnership necessity for early stage
    if project.business_stage in {"idea", "validation"}:
        if len(canvas.key_partnerships.recommendations) > 4:
            warnings.append(
                "Advisory: At the early idea/validation stage, relying on too many external partnerships "
                "can create dependency risks before product-market fit."
            )

    # Ensure validation experiments are present
    all_blocks = [
        canvas.customer_segments,
        canvas.value_propositions,
        canvas.channels,
        canvas.customer_relationships,
        canvas.revenue_streams,
        canvas.key_resources,
        canvas.key_activities,
        canvas.key_partnerships,
        canvas.cost_structure,
    ]
    total_experiments = sum(len(b.validation_experiments) for b in all_blocks)
    if total_experiments < 3:
        warnings.append(
            "Advisory: Limited empirical validation experiments provided. Conduct direct user interviews."
        )

    return canvas, warnings


def evaluate_tech_stack_rules(stack: TechnologyStackData, project: Project) -> Tuple[TechnologyStackData, List[str]]:
    """Apply deterministic architectural consistency checks to Technology Stack."""
    warnings: List[str] = []

    # Check for over-engineering for solo/low-budget founders
    is_solo_or_small = (project.team_size or "").lower() in {"solo", "1", "1-2", "2-5", ""}
    low_budget = project.budget_amount is not None and project.budget_amount < 2000

    backend_tech = stack.backend.technology.lower()
    infra_tech = stack.hosting_infrastructure.technology.lower()

    if (is_solo_or_small or low_budget) and ("kubernetes" in infra_tech or "k8s" in infra_tech or "microservices" in backend_tech):
        warnings.append(
            "Advisory: Microservices or Kubernetes introduce heavy operational overhead for small teams. "
            "Consider a modular monolith deployed on PaaS like Render or Fly.io first."
        )

    # Verification disclaimer guarantee
    if "pricing is an estimate" not in stack.frontend.verification_notes.lower():
        stack.frontend.verification_notes += " Note: Live vendor pricing should be independently verified."
    if "pricing is an estimate" not in stack.backend.verification_notes.lower():
        stack.backend.verification_notes += " Note: Live vendor pricing should be independently verified."

    return stack, warnings
