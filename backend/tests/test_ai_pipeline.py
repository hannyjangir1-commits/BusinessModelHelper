"""AI generation pipeline, versioning, persistence, and failure recovery tests."""

from unittest.mock import patch
import pytest
from app.models.blueprint import Blueprint
from app.models.generation import GenerationRun
from app.models.project import Project
from app.models.user import User
from app.services.ai.client import MockAIClient
from app.services.ai.errors import AIRateLimitError, AITimeoutError
from app.services.ai.generation import generate_business_model_canvas, generate_technology_stack


def test_bmc_generation_and_versioning(db):
    user = User(
        username="ai_tester",
        email="ai@example.com",
        password_hash="fakehash",
        display_name="AI Tester",
        preferred_currency="USD",
        is_active=True,
    )
    db.add(user)
    db.flush()

    project = Project(
        user_id=user.id,
        name="MedAI Diagnosis",
        idea_description="AI-assisted clinical note analysis for private cardiology clinics.",
        industry="HealthTech",
        business_stage="validation",
        budget_amount=15000.0,
        budget_currency="USD",
        team_size="2-5",
    )
    db.add(project)
    db.commit()

    mock_client = MockAIClient()

    # 1. First generation (Version 1)
    bp_v1, warnings = generate_business_model_canvas(db, user, project, client=mock_client)
    assert bp_v1.version == 1
    assert bp_v1.module_type == "business_model"
    assert "customer_segments" in bp_v1.content_json
    assert "value_propositions" in bp_v1.content_json
    assert "cost_structure" in bp_v1.content_json

    # Check generation run record created and marked as success
    run_v1 = db.query(GenerationRun).filter(GenerationRun.project_id == project.id).first()
    assert run_v1 is not None
    assert run_v1.status == "success"
    assert run_v1.latency_ms > 0

    # 2. Second generation / Regeneration (Version 2)
    bp_v2, _ = generate_business_model_canvas(db, user, project, client=mock_client)
    assert bp_v2.version == 2

    # Verify both versions exist in database (v1 is preserved!)
    all_versions = db.query(Blueprint).filter(Blueprint.project_id == project.id).all()
    assert len(all_versions) == 2
    versions_list = [b.version for b in all_versions]
    assert 1 in versions_list
    assert 2 in versions_list


def test_tech_stack_generation(db):
    user = User(
        username="tech_tester",
        email="tech@example.com",
        password_hash="fakehash",
        display_name="Tech Tester",
        preferred_currency="USD",
        is_active=True,
    )
    db.add(user)
    db.flush()

    project = Project(
        user_id=user.id,
        name="LogiRoute",
        idea_description="Real-time freight routing software for cross-border logistics.",
        industry="Logistics",
        business_stage="mvp",
        budget_amount=5000.0,
        budget_currency="USD",
        team_size="Solo",
    )
    db.add(project)
    db.commit()

    mock_client = MockAIClient()
    bp, warnings = generate_technology_stack(db, user, project, client=mock_client)

    assert bp.version == 1
    assert bp.module_type == "technology_stack"
    content = bp.content_json
    assert "frontend" in content
    assert "backend" in content
    assert "database" in content
    assert "hosting_infrastructure" in content
    assert "third_party_services" in content


def test_ai_failure_preserves_existing_blueprint(db):
    user = User(
        username="failure_tester",
        email="failure@example.com",
        password_hash="fakehash",
        display_name="Failure Tester",
        preferred_currency="USD",
        is_active=True,
    )
    db.add(user)
    db.flush()

    project = Project(
        user_id=user.id,
        name="Resilience Test",
        idea_description="Testing resilience against upstream provider failures.",
        industry="SaaS",
        business_stage="idea",
    )
    db.add(project)
    db.commit()

    # 1. Create initial successful version
    success_client = MockAIClient()
    bp_v1, _ = generate_business_model_canvas(db, user, project, client=success_client)
    assert bp_v1.version == 1

    # 2. Simulate AI failure during regeneration (e.g. rate limit / timeout)
    failing_client = MockAIClient(should_fail=True, fail_error=AIRateLimitError("Simulated 429 rate limit"))

    with pytest.raises(AIRateLimitError):
        generate_business_model_canvas(db, user, project, client=failing_client)

    # 3. CRITICAL: Verify version 1 is STILL INTACT in database and has not been wiped or corrupted!
    existing_bps = db.query(Blueprint).filter(Blueprint.project_id == project.id).all()
    assert len(existing_bps) == 1
    assert existing_bps[0].version == 1

    # 4. Verify failed run was logged for auditing
    runs = db.query(GenerationRun).filter(GenerationRun.project_id == project.id).order_by(GenerationRun.created_at.desc()).all()
    assert len(runs) >= 2
    latest_run = runs[0]
    assert latest_run.status == "failed"
    assert latest_run.error_code == "AI_RATE_LIMIT"
