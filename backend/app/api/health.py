"""Health, liveness, and readiness check endpoints."""

from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def liveness_check() -> dict:
    """Basic liveness probe for container orchestrators and Render."""
    settings = get_settings()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready")
def readiness_check(response: Response, db: Session = Depends(get_db)) -> dict:
    """Readiness probe verifying operational database connectivity without exposing connection details."""
    settings = get_settings()
    db_status = "connected"

    try:
        # Bounded query execution timeout (3 seconds) to prevent hanging readiness probes
        db.execute(text("SELECT 1").execution_options(timeout=3))
    except Exception as e:
        logger.error("Readiness check database failure", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        db_status = "unavailable"

    ai_configured = bool(settings.gemini_api_key and settings.gemini_api_key.strip())

    return {
        "status": "ready" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "ai_provider_configured": ai_configured,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
