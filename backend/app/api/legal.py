"""Legal documents and consent verification endpoints."""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_optional_user
from app.models.legal_acceptance import LegalAcceptance
from app.models.user import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/legal", tags=["Legal"])

CURRENT_LEGAL_DOCUMENTS = {
    "terms_and_conditions": {
        "title": "Terms and Conditions",
        "version": "2026-v1.0",
        "effective_date": "2026-01-01",
        "summary": "Governs platform usage, acceptable use, ownership of ideas, and AI output disclaimers.",
    },
    "privacy_policy": {
        "title": "Privacy Policy",
        "version": "2026-v1.0",
        "effective_date": "2026-01-01",
        "summary": "Outlines data collection, server-side session management, third-party AI processing, and account deletion.",
    },
    "acceptable_use": {
        "title": "Acceptable Use Policy",
        "version": "2026-v1.0",
        "effective_date": "2026-01-01",
        "summary": "Prohibits abusive, automated, harmful, or illegal activities on the platform.",
    },
}


@router.get("/documents", response_model=ApiResponse[Dict[str, dict]])
def get_legal_document_metadata() -> ApiResponse[Dict[str, dict]]:
    """Get metadata and current versions for all legal agreements."""
    return ApiResponse(data=CURRENT_LEGAL_DOCUMENTS)


@router.get("/status", response_model=ApiResponse[Dict[str, bool]])
def get_user_legal_consent_status(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ApiResponse[Dict[str, bool]]:
    """Check if the currently authenticated user has accepted the latest document versions."""
    if not current_user:
        return ApiResponse(data={"terms_and_conditions": False, "privacy_policy": False})

    acceptances = db.execute(
        select(LegalAcceptance).where(LegalAcceptance.user_id == current_user.id)
    ).scalars().all()

    accepted_types = {
        a.document_type: a.document_version == CURRENT_LEGAL_DOCUMENTS.get(a.document_type, {}).get("version")
        for a in acceptances
    }

    return ApiResponse(
        data={
            "terms_and_conditions": accepted_types.get("terms_and_conditions", False),
            "privacy_policy": accepted_types.get("privacy_policy", False),
        }
    )
