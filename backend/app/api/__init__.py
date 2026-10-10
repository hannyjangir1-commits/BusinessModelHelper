"""API router registration."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.business_model import router as bmc_router
from app.api.copilot import router as copilot_router
from app.api.exports import router as exports_router
from app.api.financial import router as financial_router
from app.api.generations import router as generations_router
from app.api.health import router as health_router
from app.api.legal import router as legal_router
from app.api.market_research import router as market_research_router
from app.api.profile import router as profile_router
from app.api.projects import router as projects_router
from app.api.roadmap import router as roadmap_router
from app.api.technology_stack import router as tech_router
from app.api.validator import router as validator_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(projects_router)
api_router.include_router(bmc_router)
api_router.include_router(tech_router)
api_router.include_router(validator_router)
api_router.include_router(financial_router)
api_router.include_router(market_research_router)
api_router.include_router(roadmap_router)
api_router.include_router(copilot_router)
api_router.include_router(generations_router)
api_router.include_router(exports_router)
api_router.include_router(legal_router)

__all__ = ["api_router", "health_router"]
