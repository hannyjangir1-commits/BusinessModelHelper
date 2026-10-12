"""Tests for generated data history retention, version preservation, and module scoping."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import desc, func, select

from app.models.blueprint import Blueprint
from app.models.financial_model import FinancialModel
from app.models.generation import GenerationRun
from app.models.project import Project
from app.models.user import User
from app.services.financial_service import save_or_update_financial_model
from app.schemas.financial import FinancialAssumptions, FinancialSaveRequest
from app.services.project_service import (
    MAX_BLUEPRINT_VERSIONS_RETAINED,
    MAX_COMPLETED_RUNS_RETAINED,
    prune_blueprint_versions,
    prune_generation_runs,
    save_blueprint_version,
)


@pytest.fixture
def test_setup(db):
    """Seed test user and two distinct projects."""
    user = User(
        username="retention_tester",
        email="retention@example.com",
        password_hash="fakehash",
        display_name="Retention Tester",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    proj1 = Project(
        user_id=user.id,
        name="Retention Project Alpha",
        industry="SaaS",
        idea_description="Testing history retention pruning for Project Alpha",
    )
    proj2 = Project(
        user_id=user.id,
        name="Retention Project Beta",
        industry="Hardware",
        idea_description="Testing history retention pruning for Project Beta",
    )
    db.add_all([proj1, proj2])
    db.commit()
    db.refresh(proj1)
    db.refresh(proj2)

    return user, proj1, proj2


def test_blueprint_retention_retains_latest_plus_three_older(db, test_setup):
    """Saving 6 blueprint versions retains only the newest 4 versions (3, 4, 5, 6), pruning 1 and 2."""
    user, proj1, proj2 = test_setup

    # Save 6 versions for Project 1, module 'business_model'
    for v in range(1, 7):
        save_blueprint_version(
            db=db,
            project_id=proj1.id,
            module_type="business_model",
            content_json={"step": v, "summary": f"BMC version {v}"},
        )
    db.commit()

    # Query remaining versions for proj1 'business_model'
    remaining = db.execute(
        select(Blueprint.version)
        .where(
            Blueprint.project_id == proj1.id,
            Blueprint.module_type == "business_model",
        )
        .order_by(Blueprint.version.asc())
    ).scalars().all()

    # Must retain exactly 4 versions: 3, 4, 5, 6 (latest + 3 older)
    assert len(remaining) == MAX_BLUEPRINT_VERSIONS_RETAINED
    assert remaining == [3, 4, 5, 6]

    # Verify version 6 content is intact (latest/current output survived)
    latest_bp = db.execute(
        select(Blueprint)
        .where(
            Blueprint.project_id == proj1.id,
            Blueprint.module_type == "business_model",
            Blueprint.version == 6,
        )
    ).scalar_one()
    assert latest_bp.content_json["step"] == 6


def test_blueprint_retention_is_project_and_module_scoped(db, test_setup):
    """Pruning on (proj1, business_model) does not affect (proj1, technology_stack) or proj2."""
    user, proj1, proj2 = test_setup

    # Seed 2 versions of tech stack for proj1
    for v in range(1, 3):
        save_blueprint_version(
            db=db,
            project_id=proj1.id,
            module_type="technology_stack",
            content_json={"tech_v": v},
        )

    # Seed 3 versions of business_model for proj2
    for v in range(1, 4):
        save_blueprint_version(
            db=db,
            project_id=proj2.id,
            module_type="business_model",
            content_json={"proj2_v": v},
        )
    db.commit()

    # Now add 6 versions of business_model to proj1
    for v in range(1, 7):
        save_blueprint_version(
            db=db,
            project_id=proj1.id,
            module_type="business_model",
            content_json={"proj1_bmc": v},
        )
    db.commit()

    # Verify proj1 business_model was pruned to 4 versions
    proj1_bmc_count = db.execute(
        select(func.count(Blueprint.id)).where(
            Blueprint.project_id == proj1.id,
            Blueprint.module_type == "business_model",
        )
    ).scalar_one()
    assert proj1_bmc_count == 4

    # Verify proj1 technology_stack was completely untouched (still 2)
    proj1_tech_count = db.execute(
        select(func.count(Blueprint.id)).where(
            Blueprint.project_id == proj1.id,
            Blueprint.module_type == "technology_stack",
        )
    ).scalar_one()
    assert proj1_tech_count == 2

    # Verify proj2 business_model was completely untouched (still 3)
    proj2_bmc_count = db.execute(
        select(func.count(Blueprint.id)).where(
            Blueprint.project_id == proj2.id,
            Blueprint.module_type == "business_model",
        )
    ).scalar_one()
    assert proj2_bmc_count == 3


def test_generation_runs_retention_preserves_running_and_caps_completed_at_three(db, test_setup):
    """Never prune running records; retain at most 3 completed generation runs."""
    user, proj1, _ = test_setup

    # 1. Create 2 currently active/running generation runs
    running_run_1 = GenerationRun(
        project_id=proj1.id,
        user_id=user.id,
        module_type="business_model",
        status="running",
        model="gemini-3.5-flash-lite",
        prompt_version="1.0.0",
        created_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )
    running_run_2 = GenerationRun(
        project_id=proj1.id,
        user_id=user.id,
        module_type="business_model",
        status="running",
        model="gemini-3.5-flash-lite",
        prompt_version="1.0.0",
        created_at=datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc),
    )
    db.add_all([running_run_1, running_run_2])

    # 2. Create 5 completed runs (mix of success and failed) with distinct timestamps
    completed_runs = []
    for i in range(1, 6):
        completed_runs.append(
            GenerationRun(
                project_id=proj1.id,
                user_id=user.id,
                module_type="business_model",
                status="success" if i % 2 == 1 else "failed",
                model="gemini-3.5-flash-lite",
                prompt_version="1.0.0",
                created_at=datetime(2026, 1, 1, 10, i * 10, tzinfo=timezone.utc),
                completed_at=datetime(2026, 1, 1, 10, i * 10 + 2, tzinfo=timezone.utc),
            )
        )
    db.add_all(completed_runs)
    db.commit()

    # 3. Apply pruning
    pruned_count = prune_generation_runs(db, proj1.id, "business_model", keep_completed=MAX_COMPLETED_RUNS_RETAINED)
    db.commit()

    assert pruned_count == 2, "Expected 2 older completed runs to be pruned (5 total completed - 3 kept)"

    # 4. Verify running runs SURVIVED completely
    active_runs = db.execute(
        select(GenerationRun.id).where(
            GenerationRun.project_id == proj1.id,
            GenerationRun.module_type == "business_model",
            GenerationRun.status == "running",
        )
    ).scalars().all()
    assert len(active_runs) == 2
    assert running_run_1.id in active_runs
    assert running_run_2.id in active_runs

    # 5. Verify exactly 3 completed runs remain and they are the newest ones (runs 3, 4, 5)
    remaining_completed = db.execute(
        select(GenerationRun.created_at).where(
            GenerationRun.project_id == proj1.id,
            GenerationRun.module_type == "business_model",
            GenerationRun.status != "running",
        )
        .order_by(desc(GenerationRun.created_at))
    ).scalars().all()
    assert len(remaining_completed) == 3
    def to_utc(dt):
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    assert to_utc(remaining_completed[0]) == datetime(2026, 1, 1, 10, 50, tzinfo=timezone.utc)
    assert to_utc(remaining_completed[1]) == datetime(2026, 1, 1, 10, 40, tzinfo=timezone.utc)
    assert to_utc(remaining_completed[2]) == datetime(2026, 1, 1, 10, 30, tzinfo=timezone.utc)


def test_financial_models_retention_caps_versions_at_four(db, test_setup):
    """Saving 5 versions of a financial model retains only the newest 4 versions."""
    user, proj1, _ = test_setup

    assumptions = FinancialAssumptions(
        currency="USD",
        forecast_months=12,
        starting_cash=10000.0,
        monthly_fixed_expenses=1000.0,
        marketing_expenditure=500.0,
        salaries_costs=2000.0,
        expected_sales_volume=100,
        selling_price=50.0,
        variable_cost_per_unit=15.0,
        payment_processing_pct=2.9,
        monthly_growth_rate_pct=5.0,
        tax_rate_pct=15.0,
        one_time_startup_costs=0.0,
    )

    for v in range(1, 6):
        save_or_update_financial_model(
            db=db,
            user=user,
            project_id=proj1.id,
            save_request=FinancialSaveRequest(
                name=f"Financial Plan v{v}",
                assumptions=assumptions,
            ),
        )

    # Verify versions remaining
    versions = db.execute(
        select(FinancialModel.version)
        .where(FinancialModel.project_id == proj1.id)
        .order_by(FinancialModel.version.asc())
    ).scalars().all()

    assert len(versions) == 4
    assert versions == [2, 3, 4, 5]
