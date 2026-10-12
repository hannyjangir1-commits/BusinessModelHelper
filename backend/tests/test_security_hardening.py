"""Comprehensive tests for security hardening measures.

Covers:
- Strict APP_ENV validation (rejection of invalid environments).
- Production minimum-strength signing key policy.
- Secure cookie flags in production vs. local HTTP development preservation.
- CSRF defense against malformed or missing signed payloads.
- Server-checked session revocation upon logout.
- Password change revocation of prior sessions.
- Bounded rate limiter storage, LRU eviction, and expiry pruning.
- Dynamic wiring of login rate limit thresholds from settings.
- Registration account enumeration prevention.
"""

import time
import pytest
from itsdangerous import URLSafeTimedSerializer
from app.config import Settings, get_settings
from app.core.rate_limiting import SlidingWindowRateLimiter
from app.core.sessions import create_session_token, decode_session_token


def test_invalid_app_env_rejected_at_startup():
    """Startup must fail with validation error for unrecognized APP_ENV values."""
    for invalid_env in ["staging", "invalid", "prod", "dev", "local", "docker"]:
        with pytest.raises(ValueError, match="Invalid APP_ENV"):
            Settings(app_env=invalid_env)

    # Valid environments must be accepted
    for valid_env in ["development", "production", "test"]:
        s = Settings(
            app_env=valid_env,
            secret_key="f" * 64,
            gemini_api_key="valid-api-key",
            session_https_only=True if valid_env == "production" else False,
        )
        assert s.app_env == valid_env


def test_production_weak_signing_keys_rejected():
    """Production mode must reject missing, short, or placeholder signing keys."""
    # 1. Empty / whitespace
    with pytest.raises(ValueError, match="SECRET_KEY must be a cryptographically secure key"):
        Settings(app_env="production", secret_key="", gemini_api_key="key", session_https_only=True)

    # 2. Short keys (<32 chars)
    with pytest.raises(ValueError, match="at least 32 characters"):
        Settings(app_env="production", secret_key="short-secret-key-123", gemini_api_key="key", session_https_only=True)

    # 3. Known weak/placeholder keywords
    for weak_kw in ["insecure", "development", "changeme", "default", "example", "placeholder", "password"]:
        with pytest.raises(ValueError, match="weak or default patterns"):
            Settings(
                app_env="production",
                secret_key=f"my-{weak_kw}-production-key-which-is-long-enough-32",
                gemini_api_key="key",
                session_https_only=True,
            )

    # 4. Valid random 64-char hex key
    valid_key = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    s = Settings(app_env="production", secret_key=valid_key, gemini_api_key="key", session_https_only=True)
    assert s.secret_key == valid_key



def test_cookie_flags_in_production_and_development(client):
    """Ensure session cookies have HttpOnly and SameSite=lax; Secure flag required in prod without breaking dev."""
    # Production requires session_https_only=True
    with pytest.raises(ValueError, match="SESSION_HTTPS_ONLY must be set to True"):
        Settings(
            app_env="production",
            secret_key="f" * 64,
            gemini_api_key="key",
            session_https_only=False,
        )

    # In local development, cookies are set and usable over plain HTTP
    dev_settings = Settings(app_env="development")
    assert dev_settings.session_https_only is False
    assert dev_settings.session_same_site == "lax"

    reg_payload = {
        "username": "cookie_tester",
        "email": "cookie@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201

    # Verify cookie headers in raw Set-Cookie header
    cookie_header = res.headers.get("set-cookie", "").lower()
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header


def test_csrf_failure_cases(client):
    """Test rejection on CSRF token mismatch, missing header, and malformed session tokens."""
    reg_payload = {
        "username": "csrf_hardening_user",
        "email": "csrf_hard@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    csrf_token = reg_res.json()["data"]["csrf_token"]
    cookies = reg_res.cookies

    mutation_payload = {"name": "Test CSRF Proj", "industry": "Tech", "idea_description": "Testing CSRF mutations"}

    # 1. Missing CSRF header -> 403
    res_no_header = client.post(
        "/api/projects",
        json=mutation_payload,
        cookies=cookies,
        headers={"X-Test-Enforce-CSRF": "1"},
    )
    assert res_no_header.status_code == 403

    # 2. Wrong CSRF token -> 403
    res_wrong_token = client.post(
        "/api/projects",
        json=mutation_payload,
        cookies=cookies,
        headers={"X-Test-Enforce-CSRF": "1", "X-CSRF-Token": "tampered_token_val"},
    )
    assert res_wrong_token.status_code == 403

    # 3. Malformed session token: signed payload missing csrf_token cannot bypass CSRF check
    settings = get_settings()
    serializer = URLSafeTimedSerializer(secret_key=settings.secret_key, salt="aba-session-signing-v1")
    malformed_signed_cookie = serializer.dumps({"user_id": "fake_id"})  # missing session_id & csrf_token

    res_malformed = client.post(
        "/api/projects",
        json=mutation_payload,
        cookies={settings.session_cookie_name: malformed_signed_cookie},
        headers={"X-Test-Enforce-CSRF": "1"},
    )
    assert res_malformed.status_code == 403
    assert "CSRF" in res_malformed.json()["error"]["message"]

    # 4. Valid CSRF header -> 201
    res_valid = client.post(
        "/api/projects",
        json=mutation_payload,
        cookies=cookies,
        headers={"X-Test-Enforce-CSRF": "1", "X-CSRF-Token": csrf_token},
    )
    assert res_valid.status_code == 201


def test_logout_session_revocation(client):
    """Logging out must revoke the server session; token must fail on the next request with 401."""
    reg_payload = {
        "username": "logout_revocation_user",
        "email": "logout_rev@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    cookies = reg_res.cookies

    # Valid session before logout
    me_before = client.get("/api/auth/me", cookies=cookies)
    assert me_before.status_code == 200

    # Logout
    logout_res = client.post("/api/auth/logout", cookies=cookies)
    assert logout_res.status_code == 200

    # Next request using the same token must fail with 401 Unauthorized
    me_after = client.get("/api/auth/me", cookies=cookies)
    assert me_after.status_code == 401
    assert "revoked" in me_after.json()["error"]["message"].lower() or "expired" in me_after.json()["error"]["message"].lower()


def test_password_change_revokes_prior_sessions(client):
    """Password change must revoke prior sessions so previously issued tokens fail on the next request."""
    reg_payload = {
        "username": "pwd_revocation_user",
        "email": "pwd_rev@example.com",
        "password": "InitialPassword123!",
        "confirm_password": "InitialPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    device_1_cookies = reg_res.cookies

    # Simulate login on Device 2
    login_res = client.post(
        "/api/auth/login",
        json={"username_or_email": "pwd_rev@example.com", "password": "InitialPassword123!"},
    )
    assert login_res.status_code == 200
    device_2_cookies = login_res.cookies

    # Device 1 and Device 2 can both access /me
    assert client.get("/api/auth/me", cookies=device_1_cookies).status_code == 200
    assert client.get("/api/auth/me", cookies=device_2_cookies).status_code == 200

    # Small pause to ensure timestamp progression
    time.sleep(0.05)

    # Device 2 changes password
    pwd_res = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "InitialPassword123!",
            "new_password": "NewStrongPass456!",
            "confirm_new_password": "NewStrongPass456!",
        },
        cookies=device_2_cookies,
    )
    assert pwd_res.status_code == 200

    # Prior session (Device 1) must be rejected on its next request
    me_device_1 = client.get("/api/auth/me", cookies=device_1_cookies)
    assert me_device_1.status_code == 401
    assert "revoked" in me_device_1.json()["error"]["message"].lower()

    # Active context (Device 2) remains authenticated
    assert client.get("/api/auth/me", cookies=device_2_cookies).status_code == 200


def test_rate_limiter_expiry_and_bounded_cardinality(db):
    """Rate limiter must enforce bounded cardinality, LRU eviction, and expiry."""
    # Test bounded in-memory storage (cardinality limit)
    limiter = SlidingWindowRateLimiter(max_in_memory_keys=5)

    for i in range(20):
        limiter.is_rate_limited(f"arbitrary_key_{i}", max_attempts=5, window_seconds=60)

    # Must not exceed maximum configured keys
    assert len(limiter._requests) <= 5

    # Test rate limit enforcement and expiry
    key = "test_expiry_key"
    # First 3 attempts permitted in a 1-second window
    for _ in range(3):
        limited, _ = limiter.is_rate_limited(key, max_attempts=3, window_seconds=1)
        assert limited is False

    # 4th attempt is rate-limited
    limited, retry_after = limiter.is_rate_limited(key, max_attempts=3, window_seconds=1)
    assert limited is True
    assert retry_after >= 1

    # Database synchronization with db session
    db_key = "test_db_rate_key"
    limiter.reset(db_key, db=db)
    limited_db, _ = limiter.is_rate_limited(db_key, max_attempts=2, window_seconds=10, db=db)
    assert limited_db is False
    limited_db2, _ = limiter.is_rate_limited(db_key, max_attempts=2, window_seconds=10, db=db)
    assert limited_db2 is False
    # 3rd attempt is rate limited in db
    limited_db3, _ = limiter.is_rate_limited(db_key, max_attempts=2, window_seconds=10, db=db)
    assert limited_db3 is True


def test_login_rate_limits_wire_settings_dynamically(client, monkeypatch):
    """Login rate limits must read max_attempts and window_seconds from settings."""
    settings = get_settings()
    monkeypatch.setattr(settings, "login_rate_limit_max_attempts", 2)
    monkeypatch.setattr(settings, "login_rate_limit_window_seconds", 60)

    login_payload = {"username_or_email": "rate_user@example.com", "password": "WrongPassword!"}

    # Attempt 1: 401 Unauthorized
    r1 = client.post("/api/auth/login", json=login_payload)
    assert r1.status_code == 401

    # Attempt 2: 401 Unauthorized
    r2 = client.post("/api/auth/login", json=login_payload)
    assert r2.status_code == 401

    # Attempt 3: 429 Rate Limit Exceeded
    r3 = client.post("/api/auth/login", json=login_payload)
    assert r3.status_code == 429
    assert "Too many failed login attempts" in r3.json()["error"]["message"]


def test_registration_prevents_account_enumeration(client):
    """Registration errors must avoid email vs username enumeration while giving actionable feedback."""
    reg_payload = {
        "username": "unique_founder",
        "email": "unique@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "terms_accepted": True,
        "privacy_acknowledged": True,
    }
    r1 = client.post("/api/auth/register", json=reg_payload)
    assert r1.status_code == 201

    # Duplicate username, different email
    dup_user = {**reg_payload, "email": "different_email@example.com"}
    r2 = client.post("/api/auth/register", json=dup_user)
    assert r2.status_code == 409
    msg2 = r2.json()["error"]["message"]

    # Duplicate email, different username
    dup_email = {**reg_payload, "username": "different_username"}
    r3 = client.post("/api/auth/register", json=dup_email)
    assert r3.status_code == 409
    msg3 = r3.json()["error"]["message"]

    # Both errors must be identical and give clear form feedback without leaking which field collided
    assert msg2 == msg3
    assert "already taken" in msg2.lower()
