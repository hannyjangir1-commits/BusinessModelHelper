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


def test_pdf_generation_escapes_xml_special_characters():
    """Verify that user/project/blueprint text containing &, <, >, and existing entities does not break PDF generation."""
    from app.models.blueprint import Blueprint
    from app.models.roadmap_task import RoadmapTask

    project = Project(
        name="AT&T <NextGen> & 'Smart' AI > 9000",
        idea_description="Revolutionary R&D platform: <script>alert(1)</script> & margin > 80% & cost < $10k with &amp; existing entity.",
        industry="Hardware & IoT <Edge>",
        business_stage="idea",
        target_market="North America & Europe > $5B",
        target_audience="Founders & CTOs <Tech>",
        budget_amount=7500.0,
        budget_currency="USD",
        team_size="1 < 5",
    )

    bmc = Blueprint(
        module_type="business_model",
        version=1,
        content_json={
            "overview": "Overview with R&D & growth > 150% & cost < $2k",
            "key_strategic_focus": "Disruption & Scaling <Fast>",
            "customer_segments": {
                "block_title": "B2B & B2C <Enterprise>",
                "summary": "Enterprises with revenue > $10M & team < 50 &amp; partners",
                "recommendations": ["Expand into UK & EU <tier-1>", "Maintain margins > 70%"],
                "rationale": "High demand & low supply (<3 competitors)",
                "assumptions": ["Growth > 20% year-over-year & zero churn"],
                "validation_experiments": ["A/B test with cohort <Alpha> & <Beta>"],
            },
        },
    )

    tech = Blueprint(
        module_type="technology_stack",
        version=1,
        content_json={
            "architecture_summary": "Microservices with gRPC & REST <HTTP/2>",
            "estimated_monthly_infrastructure_total": "$50 - $100 & cloud credits",
            "backend": {
                "technology": "Python & Rust <async>",
                "purpose": "Core API & compute (<10ms latency)",
                "reason": "Performance > pure Python & safety",
                "estimated_cost": "< $20/mo",
                "alternatives": ["Go & Node.js", "C++ <embedded>"],
                "tradeoffs": ["Rust compile times > Python", "Memory safety <guaranteed>"],
                "verification_notes": "Pricing verified on AWS & GCP",
            },
        },
    )

    validator = Blueprint(
        module_type="validation_report",
        version=1,
        content_json={
            "overview": "Validation synthesis: Confidence > 90% & risk < threshold",
            "problem_solution_fit": {
                "problem_statement": "Manual data entry takes > 4 hrs & causes errors",
                "who_experiences_it": "Operations managers & staff <finance>",
                "frequency_and_severity": "Daily & critical (> 8/10)",
            },
            "swot_analysis": {
                "strengths": ["Speed > alternatives & cost < legacy tools"],
                "weaknesses": ["Early stage & limited integrations (<5)"],
                "opportunities": ["Market > $10B & growing"],
                "threats": ["Competitor A & Competitor B <giants>"],
            },
            "business_risks": [
                {
                    "category": "Market & Tech",
                    "description": "Adoption latency > 6 months & high switching friction",
                    "likelihood": "High > 50%",
                    "impact": "Severe <Critical>",
                    "suggested_mitigation": "Offer freemium tier & 1-click migration",
                    "recommended_next_action": "Pilot with 5 beta users & gather feedback",
                }
            ],
            "validation_experiments": [
                {
                    "experiment_name": "Landing page test & survey <v1>",
                    "hypothesis": "Conversion rate > 5% & CAC < $20",
                    "procedure": "Run Google Ads with query 'automation & speed'",
                    "success_criteria": "Signups > 100 & CTR > 3%",
                    "estimated_duration": "< 2 weeks",
                }
            ],
        },
    )

    research = Blueprint(
        module_type="market_research",
        version=1,
        content_json={
            "executive_summary": "Market research shows CAGR > 25% & unmet customer needs",
            "market_trends": [
                {
                    "trend_title": "AI & Automation in SMBs",
                    "description": "Adoption grew > 40% & costs decreased < 30%",
                    "implications_for_founder": "First-mover advantage & high retention",
                }
            ],
            "competitors": [
                {
                    "name": "LegacyCorp & Co <Old>",
                    "website": "https://legacy.com?foo=1&bar=2",
                    "estimated_pricing": "> $500/mo",
                    "key_features": ["Feature A & B", "Feature C <v2>"],
                    "differentiators": ["Ours is 10x faster & 5x cheaper <guaranteed>"],
                }
            ],
        },
    )

    tasks = [
        RoadmapTask(
            task_key="TSK-01",
            milestone="30-day",
            title="Setup CI/CD & Deploy <Staging>",
            priority="critical",
            status="in_progress",
            deliverable="Pipeline & Docker image (<50MB)",
        ),
        RoadmapTask(
            task_key="TSK-02",
            milestone="60-day",
            title="User acquisition > 100 users",
            priority="high",
            status="pending",
            deliverable="Active users & NPS > 50",
        ),
    ]

    # Must generate valid PDF bytes without ReportLab XML parsing errors
    pdf_bytes = generate_project_blueprint_pdf(
        project,
        bmc_blueprint=bmc,
        tech_blueprint=tech,
        validator_report=validator,
        research_report=research,
        roadmap_tasks=tasks,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")

