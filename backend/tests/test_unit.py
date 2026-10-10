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


def test_comprehensive_v2_pdf_generation():
    """Verify that multi-module PDF export includes Idea Validator, Financials, Market Research, and Roadmap."""
    from app.models.blueprint import Blueprint
    from app.models.financial_model import FinancialModel
    from app.models.roadmap_task import RoadmapTask

    project = Project(
        name="Fintech Pro",
        idea_description="Automated invoicing and deterministic financial planning.",
        industry="Fintech",
        business_stage="mvp",
        budget_amount=20000.0,
        budget_currency="USD",
        team_size="3",
    )

    bmc = Blueprint(
        module_type="business_model",
        version=1,
        content_json={"customer_segments": {"block_title": "Customer Segments", "summary": "B2B SaaS founders"}},
    )
    tech = Blueprint(
        module_type="technology_stack",
        version=1,
        content_json={"backend": {"technology": "FastAPI", "purpose": "API layer", "estimated_cost": "$7/mo"}},
    )
    validator = Blueprint(
        module_type="validation_report",
        version=1,
        content_json={
            "overview": "Strong founder-problem fit.",
            "swot_analysis": {"strengths": ["Fast API"], "weaknesses": ["Small team"], "opportunities": ["Growing market"], "threats": ["Big tech"]},
        },
    )
    fin = FinancialModel(
        version=1,
        currency="USD",
        projections_json={
            "summary_metrics": {"break_even_units": 45, "break_even_revenue": 4500.0, "initial_capital_required": 1200.0, "runway_months": 14.5},
            "monthly_projections": [{"month": 1, "units_sold": 10, "revenue": 1000.0, "cogs": 200.0, "gross_profit": 800.0, "operating_expenses": 500.0, "net_profit": 300.0, "closing_cash": 20500.0}],
        },
    )
    research = Blueprint(
        module_type="market_research",
        version=1,
        content_json={
            "executive_summary": "Intense market demand for financial accuracy.",
            "competitors": [{"name": "OldPlanner", "website": "https://example.com", "estimated_pricing": "$40/mo"}],
        },
    )
    tasks = [
        RoadmapTask(task_key="TSK-01", milestone="30-day", title="Build MVP", priority="critical", status="in_progress", deliverable="Deployed container"),
        RoadmapTask(task_key="TSK-02", milestone="60-day", title="Beta Testing", priority="high", status="pending", deliverable="User feedback report"),
    ]

    pdf_bytes = generate_project_blueprint_pdf(
        project,
        bmc_blueprint=bmc,
        tech_blueprint=tech,
        validator_report=validator,
        financial_model=fin,
        research_report=research,
        roadmap_tasks=tasks,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000  # Multi-page comprehensive report
    assert pdf_bytes.startswith(b"%PDF")
