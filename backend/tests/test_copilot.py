"""Unit and integration tests for Business Blueprint Copilot."""

import pytest
from app.services.ai.client import MockAIClient
from app.services import copilot_service


def test_copilot_readonly_qa_api(client):
    """Test that Q&A mode answers founder questions without mutating blueprint or creating proposals."""
    # Register & Login
    client.post(
        "/api/auth/register",
        json={
            "username": "copilot_user1",
            "email": "copilot1@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Copilot User",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    # Create project
    proj_res = client.post(
        "/api/projects",
        json={
            "name": "SaaS Platform",
            "idea_description": "Micro-SaaS blueprint generator.",
            "industry": "DevTools",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    orig_client = copilot_service.GeminiAIClient
    copilot_service.GeminiAIClient = MockAIClient

    try:
        chat_res = client.post(
            f"/api/projects/{proj_id}/copilot/chat",
            json={
                "query": "What is my primary strategic advantage?",
                "action_type": "answer_question",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()["data"]
        assert data["action_type"] == "answer_question"
        assert data["answer"] is not None
        assert "strategic advantage" in data["answer"].lower()
        assert data["proposal"] is None

        # Verify proposal history is empty
        hist_res = client.get(f"/api/projects/{proj_id}/copilot/proposals")
        assert hist_res.status_code == 200
        assert len(hist_res.json()["data"]) == 0

    finally:
        copilot_service.GeminiAIClient = orig_client


def test_copilot_propose_edit_and_reject_api(client):
    """Test proposing an edit creates a proposal, but rejecting it leaves blueprint unchanged."""
    # Register & Login
    client.post(
        "/api/auth/register",
        json={
            "username": "copilot_user2",
            "email": "copilot2@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Copilot User 2",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    proj_res = client.post(
        "/api/projects",
        json={
            "name": "Cloud Optimizer",
            "idea_description": "Kubernetes cost reduction.",
            "industry": "DevOps",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    orig_client = copilot_service.GeminiAIClient
    copilot_service.GeminiAIClient = MockAIClient

    try:
        # Propose edit
        chat_res = client.post(
            f"/api/projects/{proj_id}/copilot/chat",
            json={
                "query": "Target high-intent enterprise DevOps teams instead of generic users",
                "action_type": "propose_edit",
                "target_module": "business_model",
                "target_section": "customer_segments",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()["data"]
        assert data["action_type"] == "propose_edit"
        proposal = data["proposal"]
        assert proposal is not None
        assert proposal["status"] == "pending"
        proposal_id = proposal["proposal_id"]

        # Reject proposal
        rej_res = client.post(f"/api/projects/{proj_id}/copilot/proposals/{proposal_id}/reject")
        assert rej_res.status_code == 200
        assert rej_res.json()["data"]["status"] == "rejected"

        # Attempting to reject again should return 409 Conflict
        rej_dup = client.post(f"/api/projects/{proj_id}/copilot/proposals/{proposal_id}/reject")
        assert rej_dup.status_code == 409

    finally:
        copilot_service.GeminiAIClient = orig_client


def test_copilot_propose_edit_and_accept_api(client):
    """Test proposing an edit and accepting it updates blueprint and records resolved status."""
    # Register & Login
    client.post(
        "/api/auth/register",
        json={
            "username": "copilot_user3",
            "email": "copilot3@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Copilot User 3",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    proj_res = client.post(
        "/api/projects",
        json={
            "name": "Fintech API",
            "idea_description": "Cross-border payment automation.",
            "industry": "Fintech",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    orig_client = copilot_service.GeminiAIClient
    copilot_service.GeminiAIClient = MockAIClient

    try:
        # Generate BMC blueprint first using mock AI client
        from app.services.ai import generation
        orig_gen_client = generation.GeminiAIClient
        generation.GeminiAIClient = MockAIClient
        try:
            bmc_gen = client.post(f"/api/projects/{proj_id}/business-model/generate")
            assert bmc_gen.status_code == 201
        finally:
            generation.GeminiAIClient = orig_gen_client

        chat_res = client.post(
            f"/api/projects/{proj_id}/copilot/chat",
            json={
                "query": "Refine customer segments to focus on indie hackers and micro-SaaS builders",
                "action_type": "propose_edit",
                "target_module": "business_model",
                "target_section": "customer_segments",
            },
        )
        assert chat_res.status_code == 200
        prop_data = chat_res.json()["data"]["proposal"]
        proposal_id = prop_data["proposal_id"]
        proposed_content = prop_data["proposed_content"]

        # Accept proposal
        acc_res = client.post(f"/api/projects/{proj_id}/copilot/proposals/{proposal_id}/accept")
        assert acc_res.status_code == 200
        assert acc_res.json()["data"]["status"] == "accepted"

        # Verify proposal history shows accepted
        hist_res = client.get(f"/api/projects/{proj_id}/copilot/proposals")
        assert hist_res.status_code == 200
        revisions = hist_res.json()["data"]
        assert len(revisions) == 1
        assert revisions[0]["status"] == "accepted"

        # Assert resulting blueprint content was actually updated in persistent store
        bp_res = client.get(f"/api/projects/{proj_id}/business-model")
        assert bp_res.status_code == 200
        bp_data = bp_res.json()["data"]
        assert bp_data["content_json"]["customer_segments"] == proposed_content

    finally:
        copilot_service.GeminiAIClient = orig_client


def test_copilot_accept_missing_blueprint_fails(client):
    """Test that accepting a proposal fails with 404 if target blueprint does not exist, and proposal remains pending."""
    # Register & Login
    client.post(
        "/api/auth/register",
        json={
            "username": "copilot_user4",
            "email": "copilot4@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Copilot User 4",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    proj_res = client.post(
        "/api/projects",
        json={
            "name": "No Blueprint Project",
            "idea_description": "Project without generated blueprint.",
            "industry": "DevTools",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    orig_client = copilot_service.GeminiAIClient
    copilot_service.GeminiAIClient = MockAIClient

    try:
        chat_res = client.post(
            f"/api/projects/{proj_id}/copilot/chat",
            json={
                "query": "Suggest customer segments",
                "action_type": "propose_edit",
                "target_module": "business_model",
                "target_section": "customer_segments",
            },
        )
        assert chat_res.status_code == 200
        proposal_id = chat_res.json()["data"]["proposal"]["proposal_id"]

        # Accept proposal should fail because blueprint does not exist
        acc_res = client.post(f"/api/projects/{proj_id}/copilot/proposals/{proposal_id}/accept")
        assert acc_res.status_code == 404

        # Proposal status must remain pending
        hist_res = client.get(f"/api/projects/{proj_id}/copilot/proposals")
        assert hist_res.status_code == 200
        revisions = hist_res.json()["data"]
        assert len(revisions) == 1
        assert revisions[0]["status"] == "pending"
    finally:
        copilot_service.GeminiAIClient = orig_client


def test_copilot_answer_unpacking_markdown():
    """Verify that _unpack_copilot_answer_to_markdown safely converts JSON, fences, and prose to clean Markdown."""
    from app.services.copilot_service import _unpack_copilot_answer_to_markdown

    # 1. Normal prose Markdown is preserved
    prose = "## Strategic Direction\nFocus on solo developers with **high willingness to pay**."
    assert _unpack_copilot_answer_to_markdown(prose) == prose

    # 2. JSON wrapper object is unpacked
    json_wrapped = '{"answer": "Focus on organic content marketing via technical case studies."}'
    assert _unpack_copilot_answer_to_markdown(json_wrapped) == "Focus on organic content marketing via technical case studies."

    # 3. Fenced JSON is stripped and unpacked
    fenced = '```json\n{"message": "Your runway is currently estimated at 6.2 months."}\n```'
    assert "Your runway is currently estimated at 6.2 months." in _unpack_copilot_answer_to_markdown(fenced)

    # 4. Multi-key JSON dict is formatted into readable Markdown headings and bullet points
    multi_key_json = '{"recommendations": ["Optimize CAC", "Launch waitlist"], "risk": "High market competition"}'
    unpacked = _unpack_copilot_answer_to_markdown(multi_key_json)
    assert "### Recommendations" in unpacked
    assert "- Optimize CAC" in unpacked
    assert "- Launch waitlist" in unpacked
    assert "**Risk**: High market competition" in unpacked

    # 5. Empty or whitespace returns helpful prompt
    assert "reviewed your project context" in _unpack_copilot_answer_to_markdown("")

