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


def test_manual_task_validation_rejects_invalid_keys_and_cycles(client):
    """Verify manual task creation and update strictly reject duplicate keys, self-dependencies, missing keys, and cycles."""
    # 1. Register & login
    client.post(
        "/api/auth/register",
        json={
            "username": "dag_tester",
            "email": "dag@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "DAG Tester",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    # 2. Create project
    proj_res = client.post(
        "/api/projects",
        json={
            "name": "DAG Project",
            "idea_description": "Testing DAG validation.",
            "industry": "DevTools",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # 3. Create initial task TSK-01
    t1_res = client.post(
        f"/api/projects/{proj_id}/roadmap/tasks",
        json={
            "task_key": "TSK-01",
            "title": "Initial Task",
            "description": "First task in sequence.",
            "milestone": "30-day",
            "dependencies": [],
        },
    )
    assert t1_res.status_code == 201
    t1_id = t1_res.json()["data"]["id"]

    # 4. Attempt to create duplicate task key -> 422
    dup_res = client.post(
        f"/api/projects/{proj_id}/roadmap/tasks",
        json={
            "task_key": "TSK-01",
            "title": "Duplicate Task",
            "description": "Should be rejected.",
            "milestone": "30-day",
            "dependencies": [],
        },
    )
    assert dup_res.status_code == 422
    assert "Duplicate task key" in dup_res.json()["error"]["message"]

    # 5. Attempt self-dependency -> 422
    self_res = client.post(
        f"/api/projects/{proj_id}/roadmap/tasks",
        json={
            "task_key": "TSK-02",
            "title": "Self Dependent",
            "description": "Depends on self.",
            "milestone": "30-day",
            "dependencies": ["TSK-02"],
        },
    )
    assert self_res.status_code == 422
    assert "cannot depend on itself" in self_res.json()["error"]["message"]

    # 6. Attempt missing dependency key -> 422
    missing_res = client.post(
        f"/api/projects/{proj_id}/roadmap/tasks",
        json={
            "task_key": "TSK-02",
            "title": "Missing Dep Task",
            "description": "Depends on non-existent task.",
            "milestone": "30-day",
            "dependencies": ["TSK-99"],
        },
    )
    assert missing_res.status_code == 422
    assert "references non-existent dependency key" in missing_res.json()["error"]["message"]

    # 7. Create valid TSK-02 depending on TSK-01
    t2_res = client.post(
        f"/api/projects/{proj_id}/roadmap/tasks",
        json={
            "task_key": "TSK-02",
            "title": "Second Task",
            "description": "Depends on TSK-01.",
            "milestone": "30-day",
            "dependencies": ["TSK-01"],
        },
    )
    assert t2_res.status_code == 201
    t2_id = t2_res.json()["data"]["id"]

    # 8. Attempt update on TSK-01 to depend on TSK-02 (Cycle: TSK-01 <-> TSK-02) -> 422
    cycle_res = client.patch(
        f"/api/projects/{proj_id}/roadmap/tasks/{t1_id}",
        json={"dependencies": ["TSK-02"]},
    )
    assert cycle_res.status_code == 422
    assert "Circular dependency" in cycle_res.json()["error"]["message"]

    # Verify TSK-01 dependencies were NOT modified (transactional rollback)
    over_res = client.get(f"/api/projects/{proj_id}/roadmap")
    tasks = over_res.json()["data"]["tasks"]
    t1_fetched = next(t for t in tasks if t["id"] == t1_id)
    assert t1_fetched["dependencies"] == []


def test_generator_cleanup_is_persisted_to_db_and_blueprint(client, db):
    """Verify that when AI generates tasks with self-dependencies or missing keys, cleanup is persisted to DB and Blueprint."""
    from app.models.blueprint import Blueprint
    from app.models.roadmap_task import RoadmapTask
    from app.services import roadmap_service

    client.post(
        "/api/auth/register",
        json={
            "username": "cleanup_founder",
            "email": "cleanup@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "Cleanup Founder",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )

    proj_res = client.post(
        "/api/projects",
        json={
            "name": "Cleanup SaaS",
            "idea_description": "Testing generator persistence.",
            "industry": "DevTools",
            "business_stage": "idea",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # Custom mock returning a self-dependency and a non-existent dependency
    class DirtyMockClient:
        def generate(self, system_instruction, user_prompt):
            data = {
                "roadmap_philosophy": "Agile execution",
                "tasks": [
                    {
                        "task_key": "TSK-01",
                        "milestone": "30-day",
                        "stage": "Planning",
                        "title": "Task 1",
                        "description": "Task 1 desc",
                        "priority": "high",
                        "estimated_effort_days": 2.0,
                        "start_day": 1,
                        "duration_days": 5,
                        # Has self-dependency TSK-01 and invalid dependency TSK-99
                        "dependencies": ["TSK-01", "TSK-99"],
                    },
                    {
                        "task_key": "TSK-02",
                        "milestone": "30-day",
                        "stage": "Planning",
                        "title": "Task 2",
                        "description": "Task 2 desc",
                        "priority": "medium",
                        "estimated_effort_days": 3.0,
                        "start_day": 6,
                        "duration_days": 5,
                        # Has valid dependency TSK-01 and duplicate TSK-01
                        "dependencies": ["TSK-01", "TSK-01"],
                    },
                ],
            }
            import json
            return json.dumps(data), 100, 50, 50

    orig_client = roadmap_service.GeminiAIClient
    roadmap_service.GeminiAIClient = DirtyMockClient

    try:
        gen_res = client.post(f"/api/projects/{proj_id}/roadmap/generate")
        assert gen_res.status_code == 201

        # Check DB rows
        t1 = db.query(RoadmapTask).filter(RoadmapTask.project_id == proj_id, RoadmapTask.task_key == "TSK-01").first()
        assert t1 is not None
        # Self-dependency and invalid reference must be cleaned
        assert t1.dependencies_json == []

        t2 = db.query(RoadmapTask).filter(RoadmapTask.project_id == proj_id, RoadmapTask.task_key == "TSK-02").first()
        assert t2 is not None
        # Duplicate must be deduplicated
        assert t2.dependencies_json == ["TSK-01"]

        # Check Blueprint snapshot
        bp = db.query(Blueprint).filter(Blueprint.project_id == proj_id, Blueprint.module_type == "execution_roadmap").first()
        assert bp is not None
        bp_tasks = bp.content_json["tasks"]
        assert bp_tasks[0]["dependencies"] == []
        assert bp_tasks[1]["dependencies"] == ["TSK-01"]
    finally:
        roadmap_service.GeminiAIClient = orig_client
