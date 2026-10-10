"""Unit tests for security, schemas, business rules, and PDF generation."""

from app.core.security import hash_password, validate_password_strength, verify_password
from app.models.project import Project
from app.schemas.business_model import BusinessModelCanvasData
from app.schemas.technology_stack import TechnologyStackData
from app.services.ai.business_rules import evaluate_bmc_rules, evaluate_tech_stack_rules
from app.services.ai.client import MockAIClient
from app.services.ai.validation import extract_json_from_text, validate_bmc_response, validate_tech_stack_response
from app.services.pdf_service import generate_project_blueprint_pdf


def test_argon2id_password_hashing():
    password = "SuperSecurePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


def test_password_strength_validation():
    valid, _ = validate_password_strength("ValidPass123")
    assert valid is True

    valid, msg = validate_password_strength("short1")
    assert valid is False
    assert "at least 8" in msg

    valid, msg = validate_password_strength("nonumbershere")
    assert valid is False
    assert "number" in msg

    valid, msg = validate_password_strength("1234567890")
    assert valid is False
    assert "letter" in msg


def test_json_extraction_from_markdown():
    raw_markdown = """Here is your response:
```json
{
  "key": "value",
  "number": 42
}
```
Hope this helps!"""
    data = extract_json_from_text(raw_markdown)
    assert data == {"key": "value", "number": 42}


def test_mock_ai_bmc_response_valid():
    client = MockAIClient()
    raw_text, latency, in_tokens, out_tokens = client.generate("customer_segments", "test prompt")
    bmc_data = validate_bmc_response(raw_text)

    assert isinstance(bmc_data, BusinessModelCanvasData)
    assert bmc_data.customer_segments.block_title == "Customer Segments"
    assert len(bmc_data.value_propositions.recommendations) >= 1
    assert latency > 0
    assert in_tokens is not None
    assert out_tokens is not None


def test_mock_ai_tech_stack_response_valid():
    client = MockAIClient()
    raw_text, latency, in_tokens, out_tokens = client.generate("frontend backend database", "test prompt")
    tech_data = validate_tech_stack_response(raw_text)

    assert isinstance(tech_data, TechnologyStackData)
    assert tech_data.frontend.category == "Frontend"
    assert tech_data.backend.category == "Backend"
    assert tech_data.database.category == "Database"


def test_deterministic_business_rules():
    project = Project(
        name="Bootstrapped App",
        idea_description="Testing business rules with low budget",
        industry="SaaS",
        business_stage="idea",
        budget_amount=200.0,
        budget_currency="USD",
        team_size="Solo",
    )

    client = MockAIClient()
    raw_text, _, _, _ = client.generate("customer_segments", "test")
    bmc_data = validate_bmc_response(raw_text)

    # Force expensive channel keyword to trigger deterministic warning
    bmc_data.channels.recommendations = ["Invest heavily in billboard advertising and TV campaigns"]
    _, warnings = evaluate_bmc_rules(bmc_data, project)
    assert any("budget" in w.lower() for w in warnings)


def test_pdf_generation_produces_valid_bytes():
    project = Project(
        name="Test Venture",
        idea_description="An innovative marketplace connecting urban farmers with local restaurants.",
        industry="AgriTech",
        business_stage="prototype",
        budget_amount=5000.0,
        budget_currency="USD",
        team_size="2-5",
    )

    pdf_bytes = generate_project_blueprint_pdf(project)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF specification magic byte header
    assert pdf_bytes.startswith(b"%PDF")
