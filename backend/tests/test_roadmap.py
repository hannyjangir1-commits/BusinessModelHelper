"""Unit and API tests for Execution Roadmap, DAG validation, and Task CRUD."""

import pytest
from app.core.exceptions import ValidationError
from app.schemas.roadmap import GeneratedRoadmapData, RoadmapTaskCreateRequest, RoadmapTaskUpdateRequest
from app.services.ai.client import MockAIClient
from app.services.roadmap_service import (
    build_roadmap_prompt,
    validate_dag_dependencies,
    validate_roadmap_response,
)
from app.models.project import Project


def test_dag_cycle_detection():
    """Verify Directed Acyclic Graph validation passes valid sequences and rejects cycles."""
    # Valid acyclic tasks (A -> B -> C)
    valid_tasks = [
        {"task_key": "A", "dependencies": []},
        {"task_key": "B", "dependencies": ["A"]},
        {"task_key": "C", "dependencies": ["B"]},
    ]
    validate_dag_dependencies(valid_tasks)  # Should not raise

    # Direct self-dependency
    self_cycle = [
        {"task_key": "A", "dependencies": ["A"]},
    ]
    with pytest.raises(ValidationError) as exc:
        validate_dag_dependencies(self_cycle)
    assert "Circular dependency" in str(exc.value)

    # Multi-hop cycle (A -> B -> C -> A)
    circular_tasks = [
        {"task_key": "A", "dependencies": ["C"]},
        {"task_key": "B", "dependencies": ["A"]},
        {"task_key": "C", "dependencies": ["B"]},
    ]
    with pytest.raises(ValidationError) as exc:
        validate_dag_dependencies(circular_tasks)
    assert "Circular dependency" in str(exc.value)


def test_roadmap_response_parsing():
    """Verify AI response parses into GeneratedRoadmapData schema."""
    client = MockAIClient()
    raw_json, _, _, _ = client.generate("agile roadmap planning", "prompt")
    validated = validate_roadmap_response(raw_json)
    assert isinstance(validated, GeneratedRoadmapData)
    assert len(validated.tasks) >= 4
    assert validated.tasks[0].task_key == "TSK-01"


def test_roadmap_api_workflow(client):
    """Test generating roadmap, task status updates, custom task CRUD, and progress tracking."""
    # 1. Register and login
    client.post(
        "/api/auth/register",
        json={
            "username": "roadmap_founder",
            "email": "roadmap@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Roadmap Founder",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    # 2. Create project
    proj_res = client.post(
        "/api/projects",
        json={
            "name": "DevSaaS",
            "idea_description": "Automated pull request compliance checker.",
            "industry": "DevTools",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # 3. Generate roadmap with mock client
    from app.services import roadmap_service

    orig_client = roadmap_service.GeminiAIClient
    roadmap_service.GeminiAIClient = MockAIClient

    try:
        gen_res = client.post(f"/api/projects/{proj_id}/roadmap/generate")
        assert gen_res.status_code == 201
        assert gen_res.json()["data"]["version"] == 1

        # 4. Get overview and verify tasks & initial 0% progress
        over_res = client.get(f"/api/projects/{proj_id}/roadmap")
        assert over_res.status_code == 200
        overview = over_res.json()["data"]
        assert overview["total_tasks"] >= 4
        assert overview["completed_tasks"] == 0
        assert overview["overall_completion_percentage"] == 0.0
        tasks = overview["tasks"]
        first_task = tasks[0]

        # 5. Update first task status to "completed"
        patch_res = client.patch(
            f"/api/projects/{proj_id}/roadmap/tasks/{first_task['id']}",
            json={"status": "completed", "priority": "critical"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["data"]["status"] == "completed"

        # 6. Verify progress increased in overview
        over_res_2 = client.get(f"/api/projects/{proj_id}/roadmap")
        overview_2 = over_res_2.json()["data"]
        assert overview_2["completed_tasks"] == 1
        assert overview_2["overall_completion_percentage"] > 0.0

        # 7. Add a custom manual task
        create_task_res = client.post(
            f"/api/projects/{proj_id}/roadmap/tasks",
            json={
                "title": "Incorporate Delaware C-Corp",
                "description": "File incorporation documents with registered agent.",
                "milestone": "30-day",
                "stage": "Planning",
                "priority": "high",
                "status": "not_started",
                "estimated_effort_days": 2.0,
                "start_day": 5,
                "duration_days": 3,
                "dependencies": [],
            },
        )
        assert create_task_res.status_code == 201
        created_task = create_task_res.json()["data"]
        assert created_task["title"] == "Incorporate Delaware C-Corp"

        # 8. Delete the custom task
        del_res = client.delete(f"/api/projects/{proj_id}/roadmap/tasks/{created_task['id']}")
        assert del_res.status_code == 200
        assert del_res.json()["data"]["deleted"] is True

        # 9. Verify versions
        ver_res = client.get(f"/api/projects/{proj_id}/roadmap/versions")
        assert ver_res.status_code == 200
        assert len(ver_res.json()["data"]) >= 1

    finally:
        roadmap_service.GeminiAIClient = orig_client
