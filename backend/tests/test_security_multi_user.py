"""Multi-user security, ownership verification, and IDOR prevention tests."""

def test_multi_user_isolation_and_ownership_enforcement(client):
    # 1. Register User A
    user_a_res = client.post(
        "/api/auth/register",
        json={
            "username": "user_a",
            "email": "user_a@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    user_a_cookies = user_a_res.cookies

    # 2. User A creates a confidential project
    proj_res = client.post(
        "/api/projects",
        json={
            "name": "Secret Project A",
            "industry": "FinTech",
            "idea_description": "Proprietary high-frequency trading platform for micro-investors.",
            "business_stage": "idea",
        },
        cookies=user_a_cookies,
    )
    project_a_id = proj_res.json()["data"]["id"]

    # 3. Register User B
    user_b_res = client.post(
        "/api/auth/register",
        json={
            "username": "user_b",
            "email": "user_b@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    user_b_cookies = user_b_res.cookies

    # 4. User B attempts to access User A's project -> MUST BE REJECTED (404)
    get_res = client.get(f"/api/projects/{project_a_id}", cookies=user_b_cookies)
    assert get_res.status_code == 404
    assert get_res.json()["success"] is False

    # 5. User B attempts to modify User A's project -> MUST BE REJECTED (404)
    patch_res = client.patch(
        f"/api/projects/{project_a_id}",
        json={"name": "Compromised Project"},
        cookies=user_b_cookies,
    )
    assert patch_res.status_code == 404

    # 6. User B attempts to export User A's project PDF -> MUST BE REJECTED (404)
    export_res = client.get(f"/api/projects/{project_a_id}/export/pdf", cookies=user_b_cookies)
    assert export_res.status_code == 404

    # 7. User B attempts to delete User A's project -> MUST BE REJECTED (404)
    del_res = client.delete(f"/api/projects/{project_a_id}", cookies=user_b_cookies)
    assert del_res.status_code == 404

    # 8. Unauthenticated requests to protected endpoints return 401
    client.cookies.clear()
    unauth_res = client.get(f"/api/projects/{project_a_id}")
    assert unauth_res.status_code == 401

    unauth_me = client.get("/api/auth/me")
    assert unauth_me.status_code == 401
