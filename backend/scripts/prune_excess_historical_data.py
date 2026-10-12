"""Operator maintenance script for pruning historical generated data.

RETENTION POLICY:
- Blueprints: Retain current/latest version + up to 3 older versions (max 4 versions per project & module).
- Generation Runs: Retain at most 3 completed runs (status != 'running') per project & module. Never prunes running records.
- Financial Models: Retain current/latest version + up to 3 older versions (max 4 versions per project).

SAFETY & OPERATOR INSTRUCTIONS:
- By default, this script runs in DRY-RUN mode. No rows are modified or deleted.
- To execute changes against a live database, operator MUST:
    1. Create a complete PostgreSQL backup (e.g., pg_dump / Render snapshot).
    2. Pass the explicit `--execute` flag.
- All modifications run inside an ACID transaction and will roll back automatically on failure.

Usage:
    # Dry run (inspection only):
    python scripts/prune_excess_historical_data.py

    # Production execution (requires backup first):
    python scripts/prune_excess_historical_data.py --execute
"""

import argparse
import logging
import os
import sys
from typing import Dict, List, Tuple

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.blueprint import Blueprint
from app.models.financial_model import FinancialModel
from app.models.generation import GenerationRun
from app.models.project import Project

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("retention_cleaner")

MAX_BLUEPRINT_VERSIONS = 4
MAX_COMPLETED_RUNS = 3
MAX_FINANCIAL_VERSIONS = 4


def inspect_and_prune_blueprints(db: Session, execute: bool) -> int:
    """Find and optionally delete blueprint records exceeding the 4-version limit."""
    # Find distinct (project_id, module_type) pairs
    pairs = db.execute(
        select(Blueprint.project_id, Blueprint.module_type).distinct()
    ).all()

    total_pruned = 0
    for project_id, module_type in pairs:
        blueprints = db.execute(
            select(Blueprint.id, Blueprint.version)
            .where(
                Blueprint.project_id == project_id,
                Blueprint.module_type == module_type,
            )
            .order_by(desc(Blueprint.version))
        ).all()

        if len(blueprints) > MAX_BLUEPRINT_VERSIONS:
            excess = blueprints[MAX_BLUEPRINT_VERSIONS:]
            excess_ids = [row[0] for row in excess]
            excess_versions = [row[1] for row in excess]
            logger.info(
                f"[Blueprints] Project {project_id} | Module '{module_type}': "
                f"Total {len(blueprints)}, keeping top {MAX_BLUEPRINT_VERSIONS}. "
                f"Pruning {len(excess)} excess versions: {excess_versions}"
            )
            if execute:
                db.execute(delete(Blueprint).where(Blueprint.id.in_(excess_ids)))
            total_pruned += len(excess_ids)

    return total_pruned


def inspect_and_prune_generation_runs(db: Session, execute: bool) -> int:
    """Find and optionally delete completed generation run records exceeding the 3 completed runs limit."""
    # Never touch running records
    pairs = db.execute(
        select(GenerationRun.project_id, GenerationRun.module_type)
        .where(GenerationRun.status != "running")
        .distinct()
    ).all()

    total_pruned = 0
    for project_id, module_type in pairs:
        runs = db.execute(
            select(GenerationRun.id, GenerationRun.created_at, GenerationRun.status)
            .where(
                GenerationRun.project_id == project_id,
                GenerationRun.module_type == module_type,
                GenerationRun.status != "running",
            )
            .order_by(
                desc(func.coalesce(GenerationRun.completed_at, GenerationRun.created_at)),
                desc(GenerationRun.created_at),
            )
        ).all()

        if len(runs) > MAX_COMPLETED_RUNS:
            excess = runs[MAX_COMPLETED_RUNS:]
            excess_ids = [row[0] for row in excess]
            logger.info(
                f"[GenerationRuns] Project {project_id} | Module '{module_type}': "
                f"Total completed {len(runs)}, keeping {MAX_COMPLETED_RUNS}. "
                f"Pruning {len(excess)} older completed runs."
            )
            if execute:
                db.execute(delete(GenerationRun).where(GenerationRun.id.in_(excess_ids)))
            total_pruned += len(excess_ids)

    return total_pruned


def inspect_and_prune_financial_models(db: Session, execute: bool) -> int:
    """Find and optionally delete financial model records exceeding the 4-version limit."""
    project_ids = db.execute(
        select(FinancialModel.project_id).distinct()
    ).scalars().all()

    total_pruned = 0
    for project_id in project_ids:
        models = db.execute(
            select(FinancialModel.id, FinancialModel.version)
            .where(FinancialModel.project_id == project_id)
            .order_by(desc(FinancialModel.version))
        ).all()

        if len(models) > MAX_FINANCIAL_VERSIONS:
            excess = models[MAX_FINANCIAL_VERSIONS:]
            excess_ids = [row[0] for row in excess]
            excess_versions = [row[1] for row in excess]
            logger.info(
                f"[FinancialModels] Project {project_id}: Total {len(models)}, "
                f"keeping top {MAX_FINANCIAL_VERSIONS}. Pruning {len(excess)} excess versions: {excess_versions}"
            )
            if execute:
                db.execute(delete(FinancialModel).where(FinancialModel.id.in_(excess_ids)))
            total_pruned += len(excess_ids)

    return total_pruned


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune excess generated historical data.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute database modifications. Defaults to dry-run if omitted.",
    )
    args = parser.parse_args()

    execute_mode = args.execute
    if not execute_mode:
        logger.info("=== DRY-RUN MODE: No database rows will be deleted. Pass --execute to apply changes. ===")
    else:
        logger.warning("=== EXECUTE MODE: Deleting excess historical data within an ACID transaction. ===")

    db: Session = SessionLocal()
    try:
        pruned_bps = inspect_and_prune_blueprints(db, execute=execute_mode)
        pruned_runs = inspect_and_prune_generation_runs(db, execute=execute_mode)
        pruned_fin = inspect_and_prune_financial_models(db, execute=execute_mode)

        if execute_mode:
            db.commit()
            logger.info(
                f"Cleanup committed successfully. Total pruned: {pruned_bps} blueprints, "
                f"{pruned_runs} generation runs, {pruned_fin} financial models."
            )
        else:
            db.rollback()
            logger.info(
                f"Dry-run inspection completed. Found: {pruned_bps} excess blueprints, "
                f"{pruned_runs} excess generation runs, {pruned_fin} excess financial models."
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during historical data cleanup: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
