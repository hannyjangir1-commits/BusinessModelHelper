"""Orchestrates end-to-end AI Business Idea Validation generation, validation, and persistence."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, List, Optional, Tuple
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.models.blueprint import Blueprint
from app.models.generation import GenerationRun
from app.models.project import Project
from app.models.user import User
from app.schemas.validator import ValidationReportData
from app.services.ai.client import GeminiAIClient
from app.services.ai.prompts import PROMPT_VERSION
from app.services.project_service import prune_generation_runs, save_blueprint_version

logger = logging.getLogger(__name__)


def build_validator_prompt(project: Project) -> Tuple[str, str]:
    """Construct structured prompt for Business Idea Validation."""
    system_instruction = (
        "You are an elite Startup Validator, Venture Capital Partner, and Lean Startup strategist. "
        "Your role is to rigorously interrogate and evaluate a proposed business idea to protect founders "
        "from premature scaling, false assumptions, and market blind spots. "
        "You must return ONLY a valid, single JSON object adhering strictly to the required schema. "
        "Do not fabricate company-specific facts. Distinguish between verified observations, hypotheses, and unknowns. "
        "Do not provide generic praise. Generate neutral, non-leading customer interview questions "
        "focusing on past behavior and current workarounds, NOT questions asking if they like the idea. "
        "Output MUST be raw JSON without markdown code fences."
    )

    user_prompt = f"""
Analyze and validate the following business project:

Project Name: {project.name}
Business Idea / Problem: {project.idea_description}
Industry: {project.industry}
Business Stage: {project.business_stage}
Target Market: {project.target_market or 'Unspecified'}
Target Audience: {project.target_audience or 'Unspecified'}
Budget: {project.budget_amount or 'Bootstrapped'} {project.budget_currency}
Team Size: {project.team_size or 'Solo founder'}
Constraints: {project.constraints or 'None reported'}

Return a JSON object with this exact structure:
{{
  "overview": "<Comprehensive executive evaluation of market viability and critical bottlenecks>",
  "problem_solution_fit": {{
    "problem_statement": "<Objective definition of problem>",
    "who_experiences_it": "<Specific demographic or persona>",
    "frequency_and_severity": "<How often friction occurs and financial/time impact>",
    "existing_alternatives": ["<Existing alternative 1>", "<Existing alternative 2>"],
    "supporting_evidence": ["<Observable fact 1>", "<Observable fact 2>"],
    "missing_evidence": ["<Critical unknown 1>", "<Critical unknown 2>"]
  }},
  "target_customer_clarity": {{
    "primary_segment": "<Beachhead customer group>",
    "secondary_segments": ["<Secondary group 1>"],
    "buyer_vs_end_user": "<Who pays vs who uses>",
    "customer_pain_points": ["<Pain point 1>", "<Pain point 2>"],
    "adoption_barriers": ["<Switching friction 1>", "<Inertia factor 2>"],
    "unvalidated_assumptions": ["<Assumption 1>", "<Assumption 2>"]
  }},
  "value_proposition_assessment": {{
    "core_benefit": "<The single main benefit>",
    "differentiation_hypotheses": ["<Differentiation hypothesis 1>", "<Differentiation hypothesis 2>"],
    "potential_weaknesses": ["<Weakness 1>", "<Weakness 2>"],
    "critical_dependencies": ["<Dependency 1>", "<Dependency 2>"],
    "key_evidence_needed": ["<Proof point needed 1>"]
  }},
  "swot_analysis": {{
    "strengths": ["<Internal strength 1>", "<Internal strength 2>"],
    "weaknesses": ["<Internal weakness 1>", "<Internal weakness 2>"],
    "opportunities": ["<External market opportunity 1>", "<External market opportunity 2>"],
    "threats": ["<External hazard/threat 1>", "<External hazard/threat 2>"]
  }},
  "business_risks": [
    {{
      "category": "Customer Adoption",
      "description": "<Specific risk>",
      "why_it_matters": "<Consequence>",
      "likelihood": "Medium",
      "impact": "High",
      "supporting_info": "<Context>",
      "suggested_mitigation": "<Mitigation>",
      "recommended_next_action": "<Concrete founder action>"
    }},
    {{
      "category": "Market",
      "description": "<Specific risk>",
      "why_it_matters": "<Consequence>",
      "likelihood": "Low",
      "impact": "High",
      "supporting_info": "<Context>",
      "suggested_mitigation": "<Mitigation>",
      "recommended_next_action": "<Concrete founder action>"
    }},
    {{
      "category": "Technology",
      "description": "<Specific risk>",
      "why_it_matters": "<Consequence>",
      "likelihood": "Medium",
      "impact": "Medium",
      "supporting_info": "<Context>",
      "suggested_mitigation": "<Mitigation>",
      "recommended_next_action": "<Concrete founder action>"
    }}
  ],
  "validation_experiments": [
    {{
      "experiment_name": "<Descriptive test name>",
      "experiment_type": "Customer Interviews",
      "hypothesis": "<Testable hypothesis>",
      "target_audience": "<Who to test with>",
      "procedure": "<Step-by-step execution>",
      "estimated_duration": "1-2 weeks",
      "estimated_cost": "$0 - $50",
      "success_criteria": "<Objective pass threshold>",
      "interpretation_guidance": "<How to pivot or proceed>"
    }},
    {{
      "experiment_name": "Landing Page Smoke Test",
      "experiment_type": "Landing Page",
      "hypothesis": "<Testable hypothesis>",
      "target_audience": "<Target audience>",
      "procedure": "<Step-by-step execution>",
      "estimated_duration": "1 week",
      "estimated_cost": "$50 - $100",
      "success_criteria": ">= 5% email conversion rate",
      "interpretation_guidance": "<How to pivot or proceed>"
    }}
  ],
  "interview_questions": [
    {{
      "question_text": "<Neutral question focusing on past friction>",
      "focus_category": "Past Behavior",
      "rationale": "<Why this reveals true intent without leading>"
    }},
    {{
      "question_text": "<Question probing current workaround and cost>",
      "focus_category": "Current Friction",
      "rationale": "<Measures current pain severity>"
    }},
    {{
      "question_text": "<Question probing who has purchasing power>",
      "focus_category": "Budget Authority",
      "rationale": "<Validates buying willingness>"
    }}
  ],
  "summary": {{
    "strongest_supporting_evidence": "<Top supporting observation>",
    "largest_uncertainties": ["<Top uncertainty 1>", "<Top uncertainty 2>"],
    "highest_priority_risks": ["<Top risk 1>"],
    "most_useful_next_experiment": "<The single most impactful experiment>",
    "unverified_assumptions": ["<Key unproven assumption>"],
    "qualitative_readiness_assessment": "Discovery Stage - High Uncertainty (Recommend 10 problem interviews before building)"
  }}
}}
"""
    return system_instruction, user_prompt


def validate_validator_response(raw_text: str) -> ValidationReportData:
    """Parse JSON and validate against ValidationReportData Pydantic schema."""
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
        return ValidationReportData.model_validate(data_dict)
    except Exception as e:
        raise ValidationError(f"AI output failed schema validation: {str(e)}")


def evaluate_validator_rules(
    data: ValidationReportData,
    project: Project,
) -> Tuple[ValidationReportData, List[str]]:
    """Apply deterministic business integrity rules to the validated report."""
    warnings: List[str] = []

    # 1. Verify likelihood and impact values
    valid_levels = {"low", "medium", "high"}
    for risk in data.business_risks:
        if risk.likelihood.lower() not in valid_levels:
            risk.likelihood = "Medium"
            warnings.append(f"Risk '{risk.description[:30]}' likelihood normalized to Medium.")
        else:
            risk.likelihood = risk.likelihood.capitalize()

        if risk.impact.lower() not in valid_levels:
            risk.impact = "Medium"
            warnings.append(f"Risk '{risk.description[:30]}' impact normalized to Medium.")
        else:
            risk.impact = risk.impact.capitalize()

    # 2. Check for leading questions
    leading_markers = ["would you buy", "do you like", "isn't it great", "would you pay"]
    for q in data.interview_questions:
        for marker in leading_markers:
            if marker in q.question_text.lower():
                warnings.append(
                    f"Interview question '{q.question_text}' flagged as potentially leading. Focus on past behavior."
                )

    return data, warnings


def generate_validation_report(
    db: Session,
    user: User,
    project: Project,
    client: Optional[Any] = None,
) -> Tuple[Blueprint, List[str]]:
    """Execute end-to-end Idea Validation generation with versioning and audit tracking."""
    ai_client = client or GeminiAIClient()
    model_name = getattr(ai_client, "model", "gemini-3.5-flash-lite")

    # 1. Audit generation run record
    run = GenerationRun(
        project_id=project.id,
        user_id=user.id,
        module_type="validation_report",
        status="running",
        model=model_name,
        prompt_version=PROMPT_VERSION,
    )
    db.add(run)
    db.commit()
    run_id = run.id

    system_instruction, user_prompt = build_validator_prompt(project)

    try:
        # 2. Invoke AI client
        raw_text, latency_ms, input_tokens, output_tokens = ai_client.generate(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        # 3. Parse and validate schema
        validated_data = validate_validator_response(raw_text)

        # 4. Apply deterministic rules
        validated_data, warnings = evaluate_validator_rules(validated_data, project)

        # 5. Save persistent blueprint safely handling concurrency
        blueprint = save_blueprint_version(
            db=db,
            project_id=project.id,
            module_type="validation_report",
            content_json=validated_data.model_dump(),
        )

        # 7. Complete audit run
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
        prune_generation_runs(db, project.id, "validation_report")

        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(blueprint)
        return blueprint, warnings

    except Exception as e:
        db.rollback()
        error_code = getattr(e, "code", "VALIDATION_GENERATION_FAILED")
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
        prune_generation_runs(db, project.id, "validation_report")
        db.commit()
        logger.error(f"Validation generation failed: {error_msg}")
        raise
