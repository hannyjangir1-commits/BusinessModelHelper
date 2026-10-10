"""Tests for AI Business Idea Validator pipeline and API."""

import pytest
from app.models.blueprint import Blueprint
from app.models.generation import GenerationRun
from app.models.project import Project
from app.schemas.validator import ValidationReportData, ValidationUpdateRequest
from app.services.ai.client import MockAIClient
from app.services.ai.errors import AITimeoutError
from app.services.ai.validator_pipeline import (
    build_validator_prompt,
    evaluate_validator_rules,
    generate_validation_report,
    validate_validator_response,
)


def test_build_validator_prompt():
    """Verify prompt builder includes project context and schema requirements."""
    project = Project(
        name="CleanEnergy SaaS",
        idea_description="Solar panel efficiency monitoring with automated inverter diagnostics.",
        industry="CleanTech",
        business_stage="idea",
    )
    system_instr, user_prompt = build_validator_prompt(project)
    assert "Startup Validator" in system_instr
    assert "CleanEnergy SaaS" in user_prompt
    assert "CleanTech" in user_prompt
    assert "swot_analysis" in user_prompt


def test_validator_response_parsing_and_rules():
    """Verify JSON parsing and deterministic rule evaluations."""
    client = MockAIClient()
    raw_json, _, _, _ = client.generate("system validator instructions", "prompt")
    validated = validate_validator_response(raw_json)
    assert isinstance(validated, ValidationReportData)
    assert len(validated.business_risks) >= 3
    assert len(validated.validation_experiments) >= 2
    assert len(validated.interview_questions) >= 3

    # Test rules evaluation
    dummy_project = Project(name="Test", idea_description="Test", industry="Tech")
    cleaned_data, warnings = evaluate_validator_rules(validated, dummy_project)
    for risk in cleaned_data.business_risks:
        assert risk.likelihood in ["Low", "Medium", "High"]
        assert risk.impact in ["Low", "Medium", "High"]


def test_validation_report_api_and_versioning(client, db):
    """Test generating, retrieving, versioning, and editing validation report."""
    # 1. Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "validator_founder",
            "email": "val@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Val Founder",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    # 2. Create project
    proj_res = client.post(
        "/api/projects",
        json={
            "name": "HealthAI Diagnostics",
            "idea_description": "AI clinic triage assistant for outpatient scheduling.",
            "industry": "Healthcare",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # 3. Generate validation report (using MockAIClient via test monkeypatch)
    from app.services.ai import validator_pipeline

    orig_client = validator_pipeline.GeminiAIClient
    validator_pipeline.GeminiAIClient = MockAIClient
    try:
        # 3a. Generate validation report using primary /validator/generate endpoint
        gen_res = client.post(f"/api/projects/{proj_id}/validator/generate")
        assert gen_res.status_code == 201
        bp_data = gen_res.json()["data"]
        assert bp_data["version"] == 1
        assert bp_data["module_type"] == "validation_report"
        assert "swot_analysis" in bp_data["content_json"]
        
        # Verify interview_questions are returned as structured objects with question_text & focus_category
        interview_qs = bp_data["content_json"]["interview_questions"]
        assert len(interview_qs) > 0
        assert isinstance(interview_qs[0], dict)
        assert "question_text" in interview_qs[0]
        assert "focus_category" in interview_qs[0]
        assert len(interview_qs[0]["question_text"]) > 0

        # 4a. Fetch latest report via /validator
        get_res = client.get(f"/api/projects/{proj_id}/validator")
        assert get_res.status_code == 200
        assert get_res.json()["data"]["version"] == 1

        # 4b. Fetch latest report via legacy alias /validation
        get_res_alias = client.get(f"/api/projects/{proj_id}/validation")
        assert get_res_alias.status_code == 200
        assert get_res_alias.json()["data"]["version"] == 1

        # 5. Generate version 2 via alias /validation/generate
        gen_res_2 = client.post(f"/api/projects/{proj_id}/validation/generate")
        assert gen_res_2.status_code == 201
        assert gen_res_2.json()["data"]["version"] == 2

        # 6. List versions via /validator/versions
        ver_res = client.get(f"/api/projects/{proj_id}/validator/versions")
        assert ver_res.status_code == 200
        assert len(ver_res.json()["data"]) == 2

        # 7. Edit latest report via /validator
        current_content = get_res.json()["data"]["content_json"]
        current_content["overview"] = "Updated founder-refined validation overview."
        patch_res = client.patch(
            f"/api/projects/{proj_id}/validator",
            json={"content": current_content},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["data"]["content_json"]["overview"] == "Updated founder-refined validation overview."

        # 8. Test unauthenticated request rejection
        from fastapi.testclient import TestClient
        from app.main import app
        unauthed_client = TestClient(app)
        unauthed_res = unauthed_client.post(f"/api/projects/{proj_id}/validator/generate")
        assert unauthed_res.status_code in (401, 403)

        # 9. Test nonexistent project ID returns 404
        nonexistent_res = client.post("/api/projects/nonexistent-project-id-999/validator/generate")
        assert nonexistent_res.status_code == 404

    finally:
        validator_pipeline.GeminiAIClient = orig_client


def test_ai_failure_preserves_existing_validation_report(db):
    """Verify that a failed generation attempt does not destroy saved validation reports."""
    from app.models.user import User

    # Create user and project directly in db
    user = User(
        username="robust_user",
        email="robust@example.com",
        password_hash="fake_hash",
        display_name="Robust User",
        preferred_currency="USD",
    )
    db.add(user)
    db.commit()

    project = Project(
        user_id=user.id,
        name="Security SaaS",
        idea_description="Zero-trust authentication proxy.",
        industry="Cybersecurity",
    )
    db.add(project)
    db.commit()

    # Successful generation 1
    mock_client = MockAIClient()
    bp1, _ = generate_validation_report(db, user, project, client=mock_client)
    assert bp1.version == 1

    # Failed generation 2 with simulated timeout
    failing_client = MockAIClient(should_fail=True, fail_error=AITimeoutError("AI timed out"))
    with pytest.raises(AITimeoutError):
        generate_validation_report(db, user, project, client=failing_client)

    # Verify version 1 remains intact in database
    latest_bp = (
        db.query(Blueprint)
        .filter(Blueprint.project_id == project.id, Blueprint.module_type == "validation_report")
        .order_by(Blueprint.version.desc())
        .first()
    )
    assert latest_bp is not None
    assert latest_bp.version == 1

    # Verify audit failure was logged in GenerationRun
    failed_run = (
        db.query(GenerationRun)
        .filter(GenerationRun.project_id == project.id, GenerationRun.status == "failed")
        .first()
    )
    assert failed_run is not None
    assert failed_run.error_code == "AI_TIMEOUT"
