"""API tests for project management and persistence."""

def test_project_crud_and_search(client):
    # Register and get session
    reg_payload = {
        "username": "project_owner",
        "email": "owner@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    cookies = reg_res.cookies

    # 1. Create project
    proj_payload = {
        "name": "NeuroLearn AI",
        "industry": "EdTech",
        "idea_description": "An adaptive learning platform using AI cognitive models to personalize student STEM education.",
        "business_stage": "validation",
        "target_market": "North America",
        "target_audience": "High school AP students and independent learners",
        "budget_amount": 2500.0,
        "budget_currency": "USD",
        "team_size": "2-5",
    }
    create_res = client.post("/api/projects", json=proj_payload, cookies=cookies)
    assert create_res.status_code == 201
    proj_data = create_res.json()["data"]
    project_id = proj_data["id"]
    assert proj_data["name"] == "NeuroLearn AI"
    assert proj_data["budget_currency"] == "USD"

    # 2. Get project details
    get_res = client.get(f"/api/projects/{project_id}", cookies=cookies)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == project_id

    # 3. List projects with pagination & search
    list_res = client.get("/api/projects?search=NeuroLearn", cookies=cookies)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["pagination"]["total_count"] == 1
    assert list_data["items"][0]["name"] == "NeuroLearn AI"

    # 4. Update project details
    patch_res = client.patch(
        f"/api/projects/{project_id}",
        json={"name": "NeuroLearn Enterprise", "business_stage": "prototype"},
        cookies=cookies,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["name"] == "NeuroLearn Enterprise"
    assert patch_res.json()["data"]["business_stage"] == "prototype"

    # 5. Delete project
    del_res = client.delete(f"/api/projects/{project_id}", cookies=cookies)
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    after_del = client.get(f"/api/projects/{project_id}", cookies=cookies)
    assert after_del.status_code == 404


def test_project_list_query_count_does_not_grow_with_page_size(db):
    """Verify that get_user_projects uses bulk queries and query count is O(1), not O(N)."""
    from contextlib import contextmanager
    from sqlalchemy import event
    from app.models.user import User
    from app.models.blueprint import Blueprint
    from app.models.roadmap_task import RoadmapTask
    from app.schemas.project import ProjectCreateRequest
    from app.services.project_service import create_project, get_user_projects

    @contextmanager
    def capture_queries(engine):
        statements = []
        def listener(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)
        event.listen(engine, "before_cursor_execute", listener)
        try:
            yield statements
        finally:
            event.remove(engine, "before_cursor_execute", listener)

    # Create test user
    user = User(
        email="perf_tester@example.com",
        username="perftester",
        password_hash="fakehash",
        display_name="Perf Tester",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create 8 projects, with blueprints and roadmap tasks
    for i in range(8):
        req = ProjectCreateRequest(
            name=f"Project {i}",
            industry="Technology",
            idea_description=f"Description for project {i}",
            business_stage="validation",
        )
        p = create_project(db, user, req)
        
        # Add blueprints
        bp1 = Blueprint(
            project_id=p.id,
            module_type="business_model",
            version=1,
            content_json={"overview": f"BMC for {i}"},
        )
        bp2 = Blueprint(
            project_id=p.id,
            module_type="technology_stack",
            version=1,
            content_json={"frontend": "Next.js"},
        )
        db.add_all([bp1, bp2])

        # Add roadmap tasks for even projects
        if i % 2 == 0:
            task = RoadmapTask(
                project_id=p.id,
                user_id=user.id,
                task_key=f"TSK-{i}-1",
                milestone="30-day",
                title=f"Initial task for project {i}",
                description=f"Initial task description for project {i}",
                status="pending",
                priority="high",
            )
            db.add(task)
    db.commit()
    db.refresh(user)

    # Measure queries for page_size=2
    with capture_queries(db.get_bind()) as queries_page_2:
        results_2, total_2 = get_user_projects(db, user, page=1, page_size=2)
    count_page_2 = len(queries_page_2)

    # Measure queries for page_size=6
    with capture_queries(db.get_bind()) as queries_page_6:
        results_6, total_6 = get_user_projects(db, user, page=1, page_size=6)
    count_page_6 = len(queries_page_6)

    # Verify query count does not grow linearly with page size
    # Specifically: 1 count query + 1 projects query + 1 bulk blueprints query + 1 bulk roadmap query = 4
    assert total_2 == 8
    assert total_6 == 8
    assert len(results_2) == 2
    assert len(results_6) == 6
    assert count_page_2 == 4, f"Expected 4 queries for page_size=2, got {count_page_2}"
    assert count_page_6 == 4, f"Expected 4 queries for page_size=6, got {count_page_6}"
    assert count_page_2 == count_page_6, "Query count must be constant and not scale linearly with page size"

    # Verify response semantics are preserved
    for resp in results_6:
        assert resp.has_business_model is True
        assert resp.has_technology_stack is True
        assert resp.latest_bmc_version == 1
        assert resp.latest_tech_version == 1


def test_export_pdf_with_xml_special_characters_api(client):
    """Test full HTTP export flow with special characters &, <, > in project details."""
    reg_payload = {
        "username": "pdf_exporter",
        "email": "pdf_exporter@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    cookies = reg_res.cookies

    create_res = client.post(
        "/api/projects",
        json={
            "name": "R&D <NextGen> & 'AI' Ventures > 9000",
            "industry": "DeepTech & Robotics <v1>",
            "idea_description": "Building hardware <robotics> & software platform with margin > 50% & cost < $10k.",
            "business_stage": "validation",
        },
        cookies=cookies,
    )
    assert create_res.status_code == 201
    proj_id = create_res.json()["data"]["id"]

    pdf_res = client.get(f"/api/projects/{proj_id}/export/pdf", cookies=cookies)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")
    assert len(pdf_res.content) > 1000

