"""Production readiness regression tests covering CSRF defense, rate limiting, and config security."""

import pytest
from app.config import Settings
from app.core.exceptions import RateLimitExceededError
from app.core.rate_limiting import generation_rate_limiter
from app.models.user import User


def test_csrf_protection_on_cookie_authenticated_requests(client):
    """Verify that state-changing cookie requests require a matching X-CSRF-Token."""
    # 1. Register and get session with CSRF token
    reg_payload = {
        "username": "csrf_tester",
        "email": "csrf@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    csrf_token = reg_res.json()["data"]["csrf_token"]
    cookies = reg_res.cookies

    # 2. State-changing request with cookie but missing CSRF token -> 403 Forbidden
    proj_payload = {
        "name": "CSRF Project Test",
        "industry": "Cybersecurity",
        "idea_description": "Testing CSRF token enforcement on state mutations.",
        "business_stage": "idea",
    }
    fail_res = client.post(
        "/api/projects",
        json=proj_payload,
        cookies=cookies,
        headers={"X-Test-Enforce-CSRF": "1"},  # Enforce check in test env
    )
    assert fail_res.status_code == 403
    assert "CSRF" in fail_res.json()["error"]["message"]

    # 3. State-changing request with mismatched CSRF token -> 403 Forbidden
    mismatch_res = client.post(
        "/api/projects",
        json=proj_payload,
        cookies=cookies,
        headers={"X-Test-Enforce-CSRF": "1", "X-CSRF-Token": "invalid_wrong_token"},
    )
    assert mismatch_res.status_code == 403
    assert "CSRF" in mismatch_res.json()["error"]["message"]

    # 4. State-changing request with valid matching CSRF token -> 201 Created
    success_res = client.post(
        "/api/projects",
        json=proj_payload,
        cookies=cookies,
        headers={"X-Test-Enforce-CSRF": "1", "X-CSRF-Token": csrf_token},
    )
    assert success_res.status_code == 201
    assert success_res.json()["data"]["name"] == "CSRF Project Test"


def test_auth_me_refreshes_csrf_token(client):
    """Verify /api/auth/me returns the CSRF token in payload and headers for SPA reloads."""
    reg_payload = {
        "username": "me_refresher",
        "email": "refresher@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    original_csrf = reg_res.json()["data"]["csrf_token"]
    cookies = reg_res.cookies

    me_res = client.get("/api/auth/me", cookies=cookies)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["csrf_token"] == original_csrf
    assert me_res.headers.get("X-CSRF-Token") == original_csrf


def test_production_settings_validation_blocks_insecure_defaults():
    """Verify Settings raises validation errors when production environment has insecure configs."""
    # 1. Insecure default secret in production -> error
    with pytest.raises(ValueError, match="SECRET_KEY must be a cryptographically secure key"):
        Settings(
            app_env="production",
            secret_key="development-insecure-secret-key-change-in-production-1234567890abcdef",
            gemini_api_key="valid-gemini-key",
        )

    # 2. Missing Gemini API key in production -> error
    with pytest.raises(ValueError, match="GEMINI_API_KEY must be configured"):
        Settings(
            app_env="production",
            secret_key="f" * 64,
            gemini_api_key="",
        )

    # 3. Valid secure settings in production -> success
    prod_settings = Settings(
        app_env="production",
        secret_key="f" * 64,
        gemini_api_key="valid-key-here",
    )
    assert prod_settings.is_production is True
    assert prod_settings.gemini_model == "gemini-3.5-flash-lite"


def test_ai_generation_rate_limiter_blocks_burst_abuse():
    """Verify that generation_rate_limiter prevents rapid resource exhaustion."""
    test_key = "gen:abuse_test_user"
    generation_rate_limiter.reset(test_key)

    # First 15 attempts succeed within 60s window
    for _ in range(15):
        limited, _ = generation_rate_limiter.is_rate_limited(test_key, max_attempts=15, window_seconds=60)
        assert limited is False

    # 16th attempt is rate-limited
    limited, retry_after = generation_rate_limiter.is_rate_limited(test_key, max_attempts=15, window_seconds=60)
    assert limited is True
    assert retry_after > 0
    generation_rate_limiter.reset(test_key)


def test_health_and_readiness_endpoints_operational(client):
    """Verify that liveness /health and readiness /ready return expected payload without leaking secrets."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    h_json = health_res.json()
    assert h_json["status"] == "healthy"
    assert "SECRET_KEY" not in str(h_json)
    assert "password" not in str(h_json)

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    r_json = ready_res.json()
    assert r_json["status"] == "ready"
    assert r_json["database"] == "connected"
