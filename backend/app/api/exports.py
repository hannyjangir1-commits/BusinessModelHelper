"""PDF Export API endpoints."""

import re
from fastapi import APIRouter, Depends, Response
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.blueprint import Blueprint
from app.models.financial_model import FinancialModel
from app.models.roadmap_task import RoadmapTask
from app.models.user import User
from app.services.pdf_service import generate_project_blueprint_pdf
from app.services.project_service import get_user_project_by_id

router = APIRouter(prefix="/projects/{project_id}/export", tags=["Exports"])


@router.get("/pdf")
def export_project_blueprint_pdf(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Generate and stream a publication-ready PDF blueprint of the project."""
    project = get_user_project_by_id(db, current_user, project_id)

    # Fetch latest BMC blueprint
    bmc_bp = db.execute(
        select(Blueprint)
        .where(Blueprint.project_id == project_id, Blueprint.module_type == "business_model")
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    # Fetch latest Tech Stack blueprint
    tech_bp = db.execute(
        select(Blueprint)
        .where(Blueprint.project_id == project_id, Blueprint.module_type == "technology_stack")
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    # Fetch latest validation report blueprint
    val_report = db.execute(
        select(Blueprint)
        .where(Blueprint.project_id == project_id, Blueprint.module_type == "validation_report")
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    # Fetch latest financial model
    fin_model = db.execute(
        select(FinancialModel)
        .where(FinancialModel.project_id == project_id)
        .order_by(desc(FinancialModel.version))
    ).scalars().first()

    # Fetch latest market research blueprint
    research_report = db.execute(
        select(Blueprint)
        .where(Blueprint.project_id == project_id, Blueprint.module_type == "market_research")
        .order_by(desc(Blueprint.version))
    ).scalars().first()

    # Fetch active execution roadmap tasks
    roadmap_tasks = db.execute(
        select(RoadmapTask)
        .where(RoadmapTask.project_id == project_id)
        .order_by(RoadmapTask.start_day.asc())
    ).scalars().all()

    pdf_bytes = generate_project_blueprint_pdf(
        project,
        bmc_blueprint=bmc_bp,
        tech_blueprint=tech_bp,
        validator_report=val_report,
        financial_model=fin_model,
        research_report=research_report,
        roadmap_tasks=roadmap_tasks,
    )

    # Clean filename
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", project.name).strip("_") or "Blueprint"
    filename = f"AI_Business_Architect_{safe_name}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
