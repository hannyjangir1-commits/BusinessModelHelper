"""Concurrency tests for monotonic Blueprint version assignment."""

import concurrent.futures
import pytest
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models.blueprint import Blueprint
from app.models.project import Project
from app.models.user import User
from app.services.project_service import save_blueprint_version
from tests.conftest import TestingSessionLocal


def test_concurrent_blueprint_version_assignment(tmp_path):
    """Verify concurrent saves assign distinct, monotonic versions without colliding."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    db_file = tmp_path / "concurrency.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    with engine.connect() as con:
        con.execute(text("PRAGMA journal_mode=WAL;"))
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    init_session = SessionLocal()
    user = User(
        username="concurrency_user",
        email="concurrency@example.com",
        display_name="Concurrency User",
        password_hash="hash",
    )
    init_session.add(user)
    init_session.flush()

    project = Project(
        user_id=user.id,
        name="Concurrent Project",
        idea_description="Testing blueprint concurrency.",
        industry="SaaS",
    )
    init_session.add(project)
    init_session.commit()

    project_id = project.id
    init_session.close()

    num_threads = 5

    def save_worker(thread_idx: int):
        session = SessionLocal()
        try:
            bp = save_blueprint_version(
                db=session,
                project_id=project_id,
                module_type="business_model",
                content_json={"thread_index": thread_idx},
            )
            session.commit()
            return bp.version
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(save_worker, i) for i in range(num_threads)]
        versions = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All versions must be unique and span 1..num_threads
    assert len(versions) == num_threads
    assert sorted(versions) == list(range(1, num_threads + 1))

    # Verify rows in DB match the 4-version retention policy (latest + up to 3 older versions: 2, 3, 4, 5)
    verify_session = SessionLocal()
    db_versions = [
        row[0]
        for row in verify_session.query(Blueprint.version)
        .filter(Blueprint.project_id == project_id, Blueprint.module_type == "business_model")
        .order_by(Blueprint.version.asc())
        .all()
    ]
    verify_session.close()
    assert db_versions == list(range(num_threads - 3, num_threads + 1))


def test_unique_constraint_enforcement(db):
    """Verify database unique constraint (uq_project_module_version) is preserved."""
    user = User(
        username="constraint_user",
        email="constraint@example.com",
        display_name="Constraint User",
        password_hash="hash",
    )
    db.add(user)
    db.flush()

    project = Project(
        user_id=user.id,
        name="Constraint Project",
        idea_description="Testing constraint integrity.",
        industry="SaaS",
    )
    db.add(project)
    db.commit()

    # Insert version 1 manually
    bp1 = Blueprint(
        project_id=project.id,
        module_type="technology_stack",
        version=1,
        content_json={"data": "v1"},
    )
    db.add(bp1)
    db.commit()

    # Attempting to insert duplicate version 1 must raise IntegrityError
    bp1_dup = Blueprint(
        project_id=project.id,
        module_type="technology_stack",
        version=1,
        content_json={"data": "duplicate"},
    )
    db.add(bp1_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
