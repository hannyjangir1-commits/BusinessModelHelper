"""AI Business Architect - Local Preflight & Safety Validation Script.

Performs robust preflight checks for local Windows execution:
1. Validates that DATABASE_URL does not point to a remote or Render database.
2. Inspects GEMINI_API_KEY without exposing secrets.
3. Checks for missing Python dependencies.
4. Detects port 8000 occupancy and safely reuses existing healthy instances.
5. Checks if frontend assets are absent or stale.

Exit Codes:
  0  - Success / Ready to proceed
  2  - Safety violation: Remote database URL detected
  3  - Missing required Python dependencies
  10 - Frontend build required (assets absent or stale)
  20 - Application is already running and healthy on port 8000
  21 - Port 8000 is occupied by an unrelated or unresponsive process
  1  - General error
"""

import argparse
import json
import os
from pathlib import Path
import re
import socket
import sys
import urllib.parse
import urllib.request


def parse_dotenv(env_path: Path) -> dict[str, str]:
    """Parse key-value pairs from a .env file without external dependencies."""
    env_vars: dict[str, str] = {}
    if not env_path.is_file():
        return env_vars

    try:
        content = env_path.read_text(encoding="utf-8")
    except Exception:
        return env_vars

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_0-9]+)\s*=\s*(.*)$", line)
        if match:
            key, val = match.groups()
            val = val.strip()
            # Strip surrounding quotes if present
            if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
                val = val[1:-1]
            env_vars[key] = val

    return env_vars


def check_database_safety(repo_root: Path) -> tuple[bool, str]:
    """Validate that DATABASE_URL does not target a live remote host.

    Local startup is strictly restricted to local SQLite or localhost PostgreSQL.
    NEVER logs or exposes database URL values or credentials.
    """
    # Prefer explicit process environment, then repo root .env
    env_file = repo_root / ".env"
    file_vars = parse_dotenv(env_file)

    db_url = os.environ.get("DATABASE_URL") or file_vars.get("DATABASE_URL", "")
    db_url = db_url.strip()

    if not db_url:
        return True, "No DATABASE_URL configured; safe default will be used"

    url_lower = db_url.lower()

    # SQLite is always local file or in-memory
    if url_lower.startswith("sqlite"):
        return True, "Local SQLite configuration verified"

    # Known remote database host patterns (Render, AWS, Supabase, Neon, etc.)
    remote_host_indicators = [
        "render.com",
        "onrender.com",
        "dpg-",  # Render managed PostgreSQL prefix
        "amazonaws.com",
        "rds.amazonaws",
        "supabase.co",
        "supabase.net",
        "neon.tech",
        "cockroachlabs.cloud",
        "elephantsql.com",
        "azure.com",
        "cloudsql",
    ]

    for indicator in remote_host_indicators:
        if indicator in url_lower:
            return False, "Database URL targets a remote managed host"

    # Parse hostname
    try:
        normalized = url_lower
        if "+" in normalized.split("://")[0]:
            scheme, rest = normalized.split("://", 1)
            base_scheme = scheme.split("+")[0]
            normalized = f"{base_scheme}://{rest}"

        parsed = urllib.parse.urlparse(normalized)
        hostname = (parsed.hostname or "").lower()

        local_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "host.docker.internal"}

        if not hostname:
            return True, "No external host found in database URL"

        if hostname in local_hosts or hostname.startswith("127."):
            return True, "Local loopback host verified"

        return False, "Database URL host is not a recognized local address"
    except Exception:
        if "localhost" not in url_lower and "127.0.0.1" not in url_lower:
            return False, "Unrecognized non-local database format"
        return True, "Local database pattern detected"


def check_gemini_key_notice(repo_root: Path) -> None:
    """Print an informative notice regarding GEMINI_API_KEY without leaking secrets."""
    env_file = repo_root / ".env"
    file_vars = parse_dotenv(env_file)
    gemini_key = (os.environ.get("GEMINI_API_KEY") or file_vars.get("GEMINI_API_KEY", "")).strip()

    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        print("[NOTICE] GEMINI_API_KEY is not configured in .env.")
        print("[NOTICE] The application will start successfully with AI mock/fallback mode.")
        print("[NOTICE] To enable live AI generation, configure GEMINI_API_KEY in .env.")
    else:
        print("[INFO] AI provider configuration detected.")


def check_python_dependencies() -> list[str]:
    """Verify that essential runtime dependencies are installed."""
    required = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "alembic": "alembic",
        "sqlalchemy": "sqlalchemy",
        "pydantic": "pydantic",
        "pydantic_settings": "pydantic-settings",
    }
    missing = []
    for mod, pkg in required.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    return missing


def check_port_status(host: str = "127.0.0.1", port: int = 8000) -> tuple[str, str]:
    """Test if port 8000 is occupied, and verify if it is an active healthy instance of this app."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.8)
        res = s.connect_ex((host, port))
        if res != 0:
            return "FREE", f"Port {port} is free"

    # Port is open. Probe health endpoint to see if our app is already running.
    health_url = f"http://{host}:{port}/health"
    try:
        req = urllib.request.Request(
            health_url,
            headers={"User-Agent": "BusinessModelHelper-Launcher"},
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8", errors="replace")
                data = json.loads(body)
                app_name = data.get("app_name", "")
                status_val = data.get("status", "")
                if app_name == "AI Business Architect" or status_val == "healthy":
                    return "ALREADY_RUNNING", f"AI Business Architect is already running at http://{host}:{port}"
    except Exception:
        pass

    return "PORT_OCCUPIED", f"Port {port} is occupied by an unrelated or unresponsive process"


def check_frontend_staleness(repo_root: Path) -> tuple[bool, str]:
    """Check whether compiled frontend assets are absent or stale."""
    dist_index = repo_root / "frontend" / "dist" / "index.html"
    if not dist_index.is_file():
        return True, "Compiled frontend bundle (frontend/dist/index.html) does not exist."

    try:
        dist_mtime = dist_index.stat().st_mtime
    except OSError:
        return True, "Cannot read frontend/dist/index.html timestamp."

    # Top-level config and entry files
    top_files = [
        repo_root / "frontend" / "package.json",
        repo_root / "frontend" / "package-lock.json",
        repo_root / "frontend" / "index.html",
        repo_root / "frontend" / "vite.config.ts",
        repo_root / "frontend" / "tsconfig.json",
        repo_root / "frontend" / "tsconfig.app.json",
        repo_root / "frontend" / "tsconfig.node.json",
    ]
    for tf in top_files:
        if tf.is_file():
            try:
                if tf.stat().st_mtime > dist_mtime:
                    return True, f"Frontend configuration file '{tf.name}' is newer than built assets."
            except OSError:
                pass

    # Source files in frontend/src
    src_dir = repo_root / "frontend" / "src"
    if src_dir.is_dir():
        for root, _, files in os.walk(src_dir):
            for file in files:
                p = Path(root) / file
                try:
                    if p.stat().st_mtime > dist_mtime:
                        rel = p.relative_to(repo_root)
                        return True, f"Frontend source file '{rel}' is newer than built assets."
                except OSError:
                    pass

    return False, "Frontend production assets are up to date."


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Business Architect Local Preflight Validation")
    parser.add_argument("--check-safety", action="store_true", help="Validate database safety, env notice, and dependencies")
    parser.add_argument("--check-port", action="store_true", help="Validate port 8000 occupancy and safe instance reuse")
    parser.add_argument("--check-frontend", action="store_true", help="Check if frontend assets are absent or stale")
    parser.add_argument("--port", type=int, default=8000, help="Server port to check (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host to check (default: 127.0.0.1)")

    args = parser.parse_args()

    # Determine repo root directory (parent of scripts/)
    repo_root = Path(__file__).resolve().parent.parent

    # Mode 1: Safety & Environment check
    if args.check_safety:
        safe, reason = check_database_safety(repo_root)
        if not safe:
            print("[ERROR] ==========================================================")
            print("[ERROR] DATABASE SAFETY VIOLATION")
            print("[ERROR] A remote or hosted database was detected in your configuration.")
            print("[ERROR] Local Windows startup is strictly restricted to local databases")
            print("[ERROR] (such as SQLite or localhost PostgreSQL).")
            print("[ERROR] Connecting to a live Render or production database is prohibited.")
            print("[ERROR] Please update DATABASE_URL in .env to use a local database.")
            print("[ERROR] ==========================================================")
            return 2

        check_gemini_key_notice(repo_root)

        missing_deps = check_python_dependencies()
        if missing_deps:
            print(f"[INFO] Missing required Python package(s): {', '.join(missing_deps)}")
            return 3

        print("[INFO] Environment and database safety verified.")
        return 0

    # Mode 2: Port & Already-Running check
    if args.check_port:
        status, msg = check_port_status(host=args.host, port=args.port)
        if status == "ALREADY_RUNNING":
            print("==========================================================")
            print("[INFO] AI Business Architect is already running!")
            print(f"[INFO] Endpoint: http://{args.host}:{args.port}")
            print("[INFO] Safe instance reuse: Opening application in your browser...")
            print("==========================================================")
            return 20
        elif status == "PORT_OCCUPIED":
            print("[ERROR] ==========================================================")
            print(f"[ERROR] Port {args.port} is already in use by another process.")
            print(f"[ERROR] AI Business Architect binds to http://{args.host}:{args.port}.")
            print(f"[ERROR] Please close the application using port {args.port} or terminate")
            print("[ERROR] that process before running the launcher.")
            print("[ERROR] ==========================================================")
            return 21
        else:
            print(f"[INFO] Port {args.port} is available.")
            return 0

    # Mode 3: Frontend staleness check
    if args.check_frontend:
        needs_build, reason = check_frontend_staleness(repo_root)
        if needs_build:
            print(f"[INFO] Frontend build needed: {reason}")
            return 10
        else:
            print("[INFO] Frontend production assets verified and up to date (no rebuild needed).")
            return 0

    # Default: Run all checks sequentially
    safe, _ = check_database_safety(repo_root)
    if not safe:
        return 2

    missing_deps = check_python_dependencies()
    if missing_deps:
        return 3

    status, _ = check_port_status(host=args.host, port=args.port)
    if status == "ALREADY_RUNNING":
        return 20
    if status == "PORT_OCCUPIED":
        return 21

    needs_build, _ = check_frontend_staleness(repo_root)
    if needs_build:
        return 10

    return 0


if __name__ == "__main__":
    sys.exit(main())
