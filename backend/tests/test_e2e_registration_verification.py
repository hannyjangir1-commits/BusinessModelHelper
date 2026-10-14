"""End-to-End Verification Test for User Registration, Database Writes, and Login Continuity."""

import pytest
from argon2 import PasswordHasher
from sqlalchemy import select
from app.models.legal_acceptance import LegalAcceptance
from app.models.user import User

hasher = PasswordHasher()


def test_e2e_registration_flow_and_login_continuity(client, db):
    test_user_payload = {
        "username": "e2e_founder_2026",
        "email": "e2e_founder_2026@venture.com",
        "password": "ProductionPass2026!",
        "confirm_password": "ProductionPass2026!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
        "privacy_accepted": True,
    }

    # 1. Execute live registration request
    reg_response = client.post("/api/auth/register", json=test_user_payload)
    assert reg_response.status_code == 201, f"Registration failed: {reg_response.text}"
    reg_data = reg_response.json()

    assert reg_data["success"] is True
    assert reg_data["message"] == "Registration successful"
    user_info = reg_data["data"]["user"]
    assert user_info["username"] == "e2e_founder_2026"
    assert user_info["email"] == "e2e_founder_2026@venture.com"
    assert "password_hash" not in user_info
    assert reg_data["data"]["csrf_token"]
    assert "aba_session" in reg_response.cookies

    new_user_id = user_info["id"]

    # 2. Verify database records persisted faithfully
    db_user = db.execute(select(User).where(User.id == new_user_id)).scalar_one_or_none()
    assert db_user is not None, "User must be found in database"
    assert db_user.username == "e2e_founder_2026"
    assert db_user.email == "e2e_founder_2026@venture.com"
    assert db_user.is_active is True

    # Verify password hash uses Argon2id (starts with $argon2id$)
    assert db_user.password_hash.startswith("$argon2id$")
    assert hasher.verify(db_user.password_hash, "ProductionPass2026!")

    # Verify legal acceptance records
    legal_records = db.execute(
        select(LegalAcceptance).where(LegalAcceptance.user_id == new_user_id)
    ).scalars().all()
    assert len(legal_records) == 2, "Must create terms and privacy acceptance records"
    doc_types = {lr.document_type for lr in legal_records}
    assert "terms_and_conditions" in doc_types
    assert "privacy_policy" in doc_types

    # 3. Verify authenticated session access via /api/auth/me
    auth_cookies = {"aba_session": reg_response.cookies["aba_session"]}
    me_res = client.get("/api/auth/me", cookies=auth_cookies)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["success"] is True
    assert me_data["data"]["id"] == new_user_id

    # 4. Verify logout functionality
    logout_res = client.post("/api/auth/logout", cookies=auth_cookies)
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["logged_out"] is True

    # 5. Verify subsequent login with newly created account
    login_res = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "e2e_founder_2026@venture.com",
            "password": "ProductionPass2026!",
        },
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["data"]["user"]["id"] == new_user_id
    assert "aba_session" in login_res.cookies

    # 6. Verify duplicate registration conflict (HTTP 409)
    dup_res = client.post("/api/auth/register", json=test_user_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"
    assert "already taken" in dup_res.json()["error"]["message"]

    # 7. Verify invalid payload returns 422 with structured details
    invalid_res = client.post(
        "/api/auth/register",
        json={
            "username": "inv",
            "email": "not-valid",
            "password": "short",
            "confirm_password": "mismatch",
            "terms_accepted": False,
            "privacy_acknowledged": False,
        },
    )
    assert invalid_res.status_code == 422
    inv_err = invalid_res.json()["error"]
    assert inv_err["code"] == "VALIDATION_ERROR"
    assert "validation_errors" in inv_err["details"]
