"""API tests for authentication, sessions, and profile management."""

def test_register_and_login_flow(client):
    register_payload = {
        "username": "founder_alpha",
        "email": "alpha@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }

    # 1. Register
    reg_res = client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_json = reg_res.json()
    assert reg_json["success"] is True
    assert reg_json["data"]["user"]["username"] == "founder_alpha"
    assert "password_hash" not in reg_json["data"]["user"]
    assert "aba_session" in reg_res.cookies

    # 2. Duplicate username error
    dup_res = client.post("/api/auth/register", json=register_payload)
    assert dup_res.status_code == 409
    assert "already taken" in dup_res.json()["error"]["message"]

    # 3. Unaccepted terms error
    unaccepted_payload = {**register_payload, "username": "another_user", "email": "another@example.com", "terms_accepted": False}
    fail_terms_res = client.post("/api/auth/register", json=unaccepted_payload)
    assert fail_terms_res.status_code == 422

    # 4. Check /api/auth/me using authenticated session cookie
    me_res = client.get("/api/auth/me", cookies=reg_res.cookies)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "alpha@example.com"

    # 5. Logout
    logout_res = client.post("/api/auth/logout", cookies=reg_res.cookies)
    assert logout_res.status_code == 200

    # 6. Login with email
    login_payload = {
        "username_or_email": "alpha@example.com",
        "password": "StrongPassword123!",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert login_res.json()["success"] is True

    # 7. Login with bad password
    bad_login = client.post("/api/auth/login", json={"username_or_email": "alpha@example.com", "password": "WrongPassword!"})
    assert bad_login.status_code == 401


def test_profile_update_and_account_deletion(client):
    reg_payload = {
        "username": "profile_user",
        "email": "profile@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    cookies = reg_res.cookies

    # Update profile
    patch_res = client.patch(
        "/api/profile",
        json={"display_name": "Updated Name", "bio": "Serial entrepreneur", "preferred_currency": "EUR"},
        cookies=cookies,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["display_name"] == "Updated Name"
    assert patch_res.json()["data"]["preferred_currency"] == "EUR"

    # Change password
    pwd_res = client.post(
        "/api/auth/change-password",
        json={"current_password": "StrongPassword123!", "new_password": "NewStrongPass456!", "confirm_new_password": "NewStrongPass456!"},
        cookies=cookies,
    )
    assert pwd_res.status_code == 200

    # Delete account
    del_res = client.request(
        "DELETE",
        "/api/profile",
        json={"password": "NewStrongPass456!", "confirmation_text": "DELETE"},
        cookies=cookies,
    )
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

    # Account no longer accessible
    after_del_me = client.get("/api/auth/me", cookies=cookies)
    assert after_del_me.status_code == 401
