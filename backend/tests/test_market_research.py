"""Unit and API tests for Market and Competitor Research with source attribution."""

import pytest
from app.schemas.market_research import MarketResearchReportData
from app.services.ai.client import MockAIClient
from app.services.research.provider import (
    MockResearchProvider,
    is_safe_external_url,
)
from app.services.research.research_pipeline import (
    build_research_synthesis_prompt,
    generate_search_queries,
    validate_research_response,
)
from app.models.project import Project


def test_ssrf_url_validation():
    """Verify SSRF defense rejects loopback, private IP, non-http, and metadata endpoints."""
    # Safe public domains
    assert is_safe_external_url("https://www.google.com") is True
    assert is_safe_external_url("https://news.ycombinator.com") is True
    assert is_safe_external_url("http://github.com/features") is True

    # Dangerous / Private / Internal endpoints (Must be blocked)
    assert is_safe_external_url("http://localhost:8000") is False
    assert is_safe_external_url("http://127.0.0.1:5432") is False
    assert is_safe_external_url("http://0.0.0.0:80") is False
    assert is_safe_external_url("http://192.168.1.1/admin") is False
    assert is_safe_external_url("http://10.0.0.1/secrets") is False
    assert is_safe_external_url("http://172.16.0.1/internal") is False
    assert is_safe_external_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_external_url("ftp://example.com/file") is False
    assert is_safe_external_url("file:///etc/passwd") is False


def test_research_prompt_and_schema_validation():
    """Verify query generation, source injection, and Pydantic validation."""
    project = Project(
        name="Developer Observability Tool",
        industry="DevOps",
        idea_description="Distributed tracing without vendor lock-in.",
        business_stage="idea",
    )
    queries = generate_search_queries(project)
    assert len(queries) >= 2
    assert "DevOps" in queries[0]

    provider = MockResearchProvider()
    sources = provider.search("DevOps tools", max_results=3)
    assert len(sources) == 3

    sys_instr, prompt = build_research_synthesis_prompt(project, sources)
    assert "Competitive Intelligence" in sys_instr
    assert sources[0].url in prompt

    # Verify MockAIClient synthesis
    client = MockAIClient()
    raw_text, _, _, _ = client.generate(sys_instr, prompt)
    report = validate_research_response(raw_text, sources)
    assert isinstance(report, MarketResearchReportData)
    assert len(report.competitors) >= 2
    assert len(report.sources) == 3


def test_market_research_api_workflow(client):
    """Test generating, retrieving, versioning, and editing market research via API."""
    # 1. Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "research_founder",
            "email": "research@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Research Founder",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    # 2. Create project
    proj_res = client.post(
        "/api/projects",
        json={
            "name": "EcoPack",
            "idea_description": "Biodegradable seaweed-based packaging for e-commerce deliveries.",
            "industry": "CleanTech",
            "business_stage": "mvp",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # 3. Generate research report using test mock
    from app.services.research import research_pipeline

    orig_client = research_pipeline.GeminiAIClient
    orig_provider_getter = research_pipeline.get_research_provider
    research_pipeline.GeminiAIClient = MockAIClient
    research_pipeline.get_research_provider = lambda: MockResearchProvider()

    try:
        gen_res = client.post(f"/api/projects/{proj_id}/market-research/generate")
        assert gen_res.status_code == 201
        data = gen_res.json()["data"]
        assert data["module_type"] == "market_research"
        assert data["version"] == 1
        content = data["content_json"]
        assert "competitors" in content
        assert len(content["competitors"]) >= 2
        assert len(content["sources"]) > 0

        # 4. Fetch latest
        get_res = client.get(f"/api/projects/{proj_id}/market-research")
        # Verify both content_json and computed fields content & sources are present
        assert "content" in data
        assert "content_json" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)

        # 4. Fetch latest via both standard and alias routes
        get_res = client.get(f"/api/projects/{proj_id}/market-research")
        assert get_res.status_code == 200
        assert get_res.json()["data"]["version"] == 1
        assert "content" in get_res.json()["data"]

        # Alias route /research
        alias_get = client.get(f"/api/projects/{proj_id}/research")
        assert alias_get.status_code == 200
        assert alias_get.json()["data"]["version"] == 1

        # 5. Generate version 2
        gen_v2 = client.post(f"/api/projects/{proj_id}/market-research/generate")
        assert gen_v2.status_code == 201
        assert gen_v2.json()["data"]["version"] == 2

        # 6. List versions via both standard and alias routes
        vers_res = client.get(f"/api/projects/{proj_id}/market-research/versions")
        assert vers_res.status_code == 200
        assert len(vers_res.json()["data"]) == 2

        alias_vers = client.get(f"/api/projects/{proj_id}/research/versions")
        assert alias_vers.status_code == 200
        assert len(alias_vers.json()["data"]) == 2

        # 7. Edit latest report content
        content["executive_summary"] = "Refined executive summary with founder field notes."
        patch_res = client.patch(
            f"/api/projects/{proj_id}/market-research",
            json={"content": content},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["data"]["content_json"]["executive_summary"] == "Refined executive summary with founder field notes."

    finally:
        research_pipeline.GeminiAIClient = orig_client
        research_pipeline.get_research_provider = orig_provider_getter


def test_market_research_empty_state_and_auth_regressions(client):
    """Verify 404 on ungenerated research, 401 on unauthorized access, and structured error responses."""
    # 1. Unauthenticated request must return 401
    unauth_res = client.get("/api/projects/some-fake-id/market-research")
    assert unauth_res.status_code == 401
    assert unauth_res.json()["success"] is False

    # 2. Register user to test empty project state
    client.post(
        "/api/auth/register",
        json={
            "username": "empty_researcher",
            "email": "empty@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Empty Researcher",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    proj_res = client.post(
        "/api/projects",
        json={
            "name": "Blank Venture",
            "idea_description": "A new venture without research yet.",
            "industry": "FinTech",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # 3. Getting research before generating must return 404
    empty_res = client.get(f"/api/projects/{proj_id}/market-research")
    assert empty_res.status_code == 404
    assert empty_res.json()["success"] is False
    assert "No market research report found" in empty_res.json()["error"]["message"]

    # 4. Unknown API endpoint returns 404 JSON, not an HTML page
    unknown_api_res = client.get("/api/projects/unknown-route/nonexistent")
    assert unknown_api_res.status_code == 404
    assert unknown_api_res.headers["content-type"].startswith("application/json")
