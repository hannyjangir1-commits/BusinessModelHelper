"""Financial Projection Engine API endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.financial import (
    FinancialModelResponse,
    FinancialRecalculateRequest,
    FinancialSaveRequest,
)
from app.services.financial_service import (
    compute_full_financial_model,
    delete_financial_model,
    generate_financial_ai_advisory,
    get_financial_model,
    list_financial_model_versions,
    save_or_update_financial_model,
)
from app.services.project_service import get_user_project_by_id

router = APIRouter(prefix="/projects/{project_id}/financial", tags=["Financial Projections"])


@router.post("", response_model=ApiResponse[FinancialModelResponse], status_code=status.HTTP_201_CREATED)
def create_or_save_financial_model(
    project_id: str,
    save_req: FinancialSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FinancialModelResponse]:
    """Persist financial assumptions and deterministic projections to database."""
    model = save_or_update_financial_model(db, current_user, project_id, save_req)
    return ApiResponse(data=model, message="Financial projection model saved successfully.")


@router.get("", response_model=ApiResponse[FinancialModelResponse])
def get_latest_or_version_financial_model(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific version number; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FinancialModelResponse]:
    """Retrieve saved financial model for project."""
    model = get_financial_model(db, current_user, project_id, version=version)
    return ApiResponse(data=model)


@router.get("/versions", response_model=ApiResponse[List[Dict[str, Any]]])
def list_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[Dict[str, Any]]]:
    """List all saved financial model versions."""
    versions = list_financial_model_versions(db, current_user, project_id)
    return ApiResponse(data=versions)


@router.post("/calculate", response_model=ApiResponse[FinancialModelResponse])
def preview_recalculation(
    project_id: str,
    calc_req: FinancialRecalculateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FinancialModelResponse]:
    """Perform deterministic recalculation in Python without saving to database."""
    get_user_project_by_id(db, current_user, project_id)  # verify ownership
    computed = compute_full_financial_model(
        assumptions=calc_req.assumptions,
        project_id=project_id,
        name="Interactive Preview",
    )
    return ApiResponse(data=computed, message="Recalculated projections successfully.")


@router.post("/ai-advisor", response_model=ApiResponse[Dict[str, str]])
def get_ai_cfo_advisory(
    project_id: str,
    version: Optional[int] = Query(None, description="Specific version number; defaults to latest"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[Dict[str, str]]:
    """Generate strategic AI advisory commentary grounded strictly in the calculated numbers."""
    project = get_user_project_by_id(db, current_user, project_id)
    model = get_financial_model(db, current_user, project_id, version=version)
    advisory_text = generate_financial_ai_advisory(project, model)
    return ApiResponse(data={"advisory": advisory_text})


@router.delete("/{model_id}", response_model=ApiResponse[dict])
def remove_model(
    project_id: str,
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Delete a specific financial model."""
    delete_financial_model(db, current_user, project_id, model_id)
    return ApiResponse(data={"deleted": True}, message="Financial model deleted successfully.")
