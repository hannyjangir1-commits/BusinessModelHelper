"""Orchestrates end-to-end AI generation pipeline, persistence, versioning, and error auditing."""

from datetime import datetime, timezone
import logging
from typing import Any, List, Optional, Tuple
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.models.blueprint import Blueprint
from app.models.generation import GenerationRun
from app.models.project import Project
from app.models.user import User
from app.schemas.business_model import BusinessModelCanvasData
from app.schemas.technology_stack import TechnologyStackData
from app.services.ai.business_rules import evaluate_bmc_rules, evaluate_tech_stack_rules
from app.services.ai.client import GeminiAIClient
from app.services.ai.prompts import PROMPT_VERSION, build_bmc_prompt, build_tech_stack_prompt
from app.services.ai.validation import validate_bmc_response, validate_tech_stack_response
from app.services.project_service import prune_generation_runs, save_blueprint_version

logger = logging.getLogger(__name__)


def generate_business_model_canvas(
    db: Session,
    user: User,
    project: Project,
    client: Optional[Any] = None,
) -> Tuple[Blueprint, List[str]]:
    """Execute end-to-end Business Model Canvas generation with versioning and audit tracking."""
    ai_client = client or GeminiAIClient()
    model_name = getattr(ai_client, "model", "gemini-3.5-flash-lite")

    # 1. Create audit generation run record
    run = GenerationRun(
        project_id=project.id,
        user_id=user.id,
        module_type="business_model",
        status="running",
        model=model_name,
        prompt_version=PROMPT_VERSION,
    )
    db.add(run)
    db.commit()
    run_id = run.id

    system_instruction, user_prompt = build_bmc_prompt(project)

    try:
        # 2. Invoke AI Client
        raw_text, latency_ms, input_tokens, output_tokens = ai_client.generate(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        # 3. Parse and validate Pydantic schema
        validated_data = validate_bmc_response(raw_text)

        # 4. Apply deterministic business rules
        validated_data, warnings = evaluate_bmc_rules(validated_data, project)

        # 5. Save persistent blueprint safely handling concurrency
        blueprint = save_blueprint_version(
            db=db,
            project_id=project.id,
            module_type="business_model",
            content_json=validated_data.model_dump(),
        )

        # 7. Complete audit run record and enforce retention limit
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
        prune_generation_runs(db, project.id, "business_model")

        # Update project timestamp
        project.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(blueprint)
        return blueprint, warnings

    except Exception as e:
        db.rollback()
        error_code = getattr(e, "code", "AI_GENERATION_FAILED")
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
        prune_generation_runs(db, project.id, "business_model")
        db.commit()

        logger.error(
            "AI BMC Generation failed",
            extra={
                "extra_fields": {
                    "project_id": project.id,
                    "error_code": error_code,
                    "error_message": error_msg,
                }
            },
        )
        raise


def generate_technology_stack(
    db: Session,
    user: User,
    project: Project,
    client: Optional[Any] = None,
) -> Tuple[Blueprint, List[str]]:
    """Execute end-to-end Technology Stack generation with versioning and audit tracking."""
    ai_client = client or GeminiAIClient()
    model_name = getattr(ai_client, "model", "gemini-3.5-flash-lite")

    # 1. Create audit generation run record
    run = GenerationRun(
        project_id=project.id,
        user_id=user.id,
        module_type="technology_stack",
        status="running",
        model=model_name,
        prompt_version=PROMPT_VERSION,
    )
    db.add(run)
    db.commit()
    run_id = run.id

    system_instruction, user_prompt = build_tech_stack_prompt(project)

    try:
        # 2. Invoke AI Client
        raw_text, latency_ms, input_tokens, output_tokens = ai_client.generate(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        # 3. Parse and validate Pydantic schema
        validated_data = validate_tech_stack_response(raw_text)

        # 4. Apply deterministic business rules
        validated_data, warnings = evaluate_tech_stack_rules(validated_data, project)

        # 5. Save persistent blueprint safely handling concurrency
        blueprint = save_blueprint_version(
            db=db,
            project_id=project.id,
            module_type="technology_stack",
            content_json=validated_data.model_dump(),
        )

        # 7. Complete audit run record and enforce retention limit
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
        prune_generation_runs(db, project.id, "technology_stack")

        # Update project timestamp
        project.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(blueprint)
        return blueprint, warnings

    except Exception as e:
        db.rollback()
        error_code = getattr(e, "code", "AI_GENERATION_FAILED")
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
        prune_generation_runs(db, project.id, "technology_stack")
        db.commit()

        logger.error(
            "AI Tech Stack Generation failed",
            extra={
                "extra_fields": {
                    "project_id": project.id,
                    "error_code": error_code,
                    "error_message": error_msg,
                }
            },
        )
        raise
