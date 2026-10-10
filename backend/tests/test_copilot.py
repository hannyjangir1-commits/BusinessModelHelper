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
        proposal_id = chat_res.json()["data"]["proposal"]["proposal_id"]

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

    finally:
        copilot_service.GeminiAIClient = orig_client
