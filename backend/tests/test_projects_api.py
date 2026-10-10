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
