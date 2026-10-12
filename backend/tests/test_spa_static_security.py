"""Regression tests for SPA catch-all and static file path traversal defense.

Tests cover:
- Ordinary static files served correctly from static root.
- SPA routes fallback to index.html for client-side navigation.
- Missing file paths (with extensions) return 404 rather than faux HTML.
- Traversal variants (relative parent directories, nested traversal, encoded dots/slashes) are rejected.
- Symlink escapes pointing outside static root are rejected when supported by the OS.
- API and health endpoints remain unaffected.
- No real environment variables or host secrets are read; uses isolated temporary sentinel.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

SENTINEL_CONTENT = "HARMLESS_TEST_SENTINEL_TOKEN_XYZ_84729"


@pytest.fixture
def temp_spa_env(tmp_path, monkeypatch):
    """Set up an isolated static root and a harmless sentinel file outside the root."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    # Dist files
    (dist_dir / "index.html").write_text("<!DOCTYPE html><html><body>SPA Root</body></html>", encoding="utf-8")
    (dist_dir / "app.js").write_text("console.log('aba-test-app');", encoding="utf-8")
    (dist_dir / "style.css").write_text("body { margin: 0; background: #fff; }", encoding="utf-8")

    sub_dir = dist_dir / "icons"
    sub_dir.mkdir()
    (sub_dir / "logo.svg").write_text("<svg id='logo'></svg>", encoding="utf-8")

    # Sentinel file outside the static root
    sentinel_file = tmp_path / "sentinel.txt"
    sentinel_file.write_text(SENTINEL_CONTENT, encoding="utf-8")

    # Check symlink support
    symlink_supported = False
    symlink_file = dist_dir / "symlink_escape.txt"
    try:
        symlink_file.symlink_to(sentinel_file)
        symlink_supported = True
    except (OSError, NotImplementedError):
        pass

    # Monkeypatch static_dist_path in app.main
    monkeypatch.setattr("app.main.static_dist_path", dist_dir)

    return {
        "dist_dir": dist_dir,
        "sentinel_file": sentinel_file,
        "symlink_supported": symlink_supported,
    }


def test_ordinary_static_files_served_correctly(temp_spa_env, client: TestClient):
    """Ordinary files inside the static root should be served with appropriate content."""
    # Root static file
    res_js = client.get("/app.js")
    assert res_js.status_code == 200
    assert "console.log('aba-test-app');" in res_js.text

    # CSS file
    res_css = client.get("/style.css")
    assert res_css.status_code == 200
    assert "background: #fff;" in res_css.text

    # Subdirectory static file
    res_svg = client.get("/icons/logo.svg")
    assert res_svg.status_code == 200
    assert "<svg id='logo'></svg>" in res_svg.text



def test_valid_spa_routes_return_200_with_spa_shell(temp_spa_env, client: TestClient):
    """Valid static and dynamic client-side routes should return HTTP 200 with the SPA index.html shell."""
    valid_routes = [
        "/",
        "/terms",
        "/privacy",
        "/acceptable-use",
        "/contact",
        "/login",
        "/register",
        "/dashboard",
        "/profile",
        "/projects/new",
        "/projects/123",
        "/projects/123/canvas",
        "/projects/proj-abc-456/threats",
    ]
    for path in valid_routes:
        res = client.get(path)
        assert res.status_code == 200, f"Expected 200 for valid route {path}, got {res.status_code}"
        assert "<!DOCTYPE html>" in res.text
        assert "SPA Root" in res.text


def test_unknown_client_routes_return_404_with_spa_shell(temp_spa_env, client: TestClient):
    """Unrecognized client routes should return HTTP 404 while serving the SPA shell for client-side rendering."""
    unknown_routes = [
        "/nonexistent",
        "/unknown/route",
        "/auth/login",  # Legacy non-existent path
        "/settings/profile",  # Legacy non-existent path
        "/projects",  # Missing project ID or action
        "/projects/123/canvas/too/deep/route",
    ]
    for path in unknown_routes:
        res = client.get(path)
        assert res.status_code == 404, f"Expected 404 for unknown client route {path}, got {res.status_code}"
        assert "<!DOCTYPE html>" in res.text, f"Expected SPA shell in 404 response for {path}"
        assert "SPA Root" in res.text


def test_missing_file_paths_return_404_json(temp_spa_env, client: TestClient):
    """Missing asset files with extensions must return HTTP 404 JSON and never fall through to the SPA shell."""
    for path in ["/missing.css", "/missing.js", "/assets/nonexistent.png", "/favicon_missing.ico", "/bundle.map"]:
        res = client.get(path)
        assert res.status_code == 404
        assert SENTINEL_CONTENT not in res.text
        assert "SPA Root" not in res.text
        assert res.headers.get("content-type", "").startswith("application/json")


def test_path_traversal_variants_blocked(temp_spa_env, client: TestClient):
    """Path traversal attempts targeting outside files must return 404 and never leak content."""
    traversal_paths = [
        "/../sentinel.txt",
        "/../../sentinel.txt",
        "/../../../sentinel.txt",
        "/assets/../../sentinel.txt",
        "/assets/../sentinel.txt",
        "/..%2f..%2fsentinel.txt",
        "/%2e%2e/%2e%2e/sentinel.txt",
        "/%2e%2e/sentinel.txt",
        "/..\\..\\sentinel.txt",
    ]

    for path in traversal_paths:
        res = client.get(path)
        assert res.status_code == 404, f"Traversal path {path} returned status {res.status_code}"
        assert SENTINEL_CONTENT not in res.text, f"Sentinel content leaked by {path}"


def test_symlink_escape_blocked_if_supported(temp_spa_env, client: TestClient):
    """Symlink pointing outside static root must be rejected if the OS supports symlinks."""
    if not temp_spa_env["symlink_supported"]:
        pytest.skip(
            "Symlink creation not supported in this test environment/permissions "
            "(Windows WinError 1314: SeCreateSymbolicLinkPrivilege requires Admin or Developer Mode)."
        )

    res = client.get("/symlink_escape.txt")
    assert res.status_code == 404
    assert SENTINEL_CONTENT not in res.text


def test_api_and_health_routes_preserved(temp_spa_env, client: TestClient):
    """Excluded routing for health, ready, and API endpoints must continue to operate."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"

    api_404 = client.get("/api/nonexistent_test_route")
    assert api_404.status_code == 404
    assert api_404.json()["error"]["code"] == "NOT_FOUND"


def test_backend_frontend_routes_aligned():
    """Verify that backend recognized static client routes stay aligned with frontend/src/App.tsx."""
    from pathlib import Path
    import re
    from app.main import RECOGNIZED_STATIC_CLIENT_ROUTES, is_valid_client_route

    app_tsx = Path(__file__).resolve().parents[2] / "frontend" / "src" / "App.tsx"
    assert app_tsx.exists(), "frontend/src/App.tsx must exist"
    app_content = app_tsx.read_text(encoding="utf-8")

    # Extract all exact path comparisons in App.tsx: e.g. currentPath === '/terms'
    route_matches = re.findall(r"currentPath\s*===\s*['\"]([^'\"]+)['\"]", app_content)
    assert len(route_matches) > 0, "Failed to find routes in App.tsx"

    for route in route_matches:
        clean = route.strip("/")
        assert clean in RECOGNIZED_STATIC_CLIENT_ROUTES, f"Route '{route}' from App.tsx missing in backend RECOGNIZED_STATIC_CLIENT_ROUTES"
        assert is_valid_client_route(route) is True, f"Route '{route}' must be recognized by is_valid_client_route"

    # Verify dynamic project routes match App.tsx dynamic prefix
    assert is_valid_client_route("/projects/123") is True
    assert is_valid_client_route("/projects/new") is True
    assert is_valid_client_route("/projects/abc-xyz/overview") is True
    # In App.tsx, bare /projects does not match currentPath.startsWith('/projects/')
    assert is_valid_client_route("/projects") is False
    assert is_valid_client_route("/random_unrecognized_route") is False

