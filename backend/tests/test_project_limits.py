"""Tests for per-user project cap enforcement, concurrency safety, and account isolation."""

import concurrent.futures
import pytest
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreateRequest
from app.services.project_service import MAX_PROJECTS_PER_USER, create_project, delete_project


def test_exactly_three_projects_allowed_fourth_rejected(client):
    """Verify that a user can create exactly 3 projects, and project 4 is rejected with 403 PROJECT_LIMIT_REACHED."""
    # 1. Register User A
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "limit_user_1",
            "email": "limit1@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    assert reg_res.status_code == 201
    cookies = reg_res.cookies

    # 2. Successfully create project 1, 2, 3
    created_ids = []
    for i in range(1, 4):
        create_res = client.post(
            "/api/projects",
            json={
                "name": f"Venture {i}",
                "industry": "Fintech",
                "idea_description": f"Detailed business description for venture {i}",
                "business_stage": "idea",
            },
            cookies=cookies,
        )
        assert create_res.status_code == 201, f"Project {i} should be successfully created"
        created_ids.append(create_res.json()["data"]["id"])

    # 3. Attempting project 4 must fail with 403 Forbidden and PROJECT_LIMIT_REACHED
    fourth_res = client.post(
        "/api/projects",
        json={
            "name": "Venture 4 - Overflow",
            "industry": "Fintech",
            "idea_description": "This fourth project should be rejected by the per-user cap.",
            "business_stage": "idea",
        },
        cookies=cookies,
    )
    assert fourth_res.status_code == 403
    err_body = fourth_res.json()
    assert err_body["success"] is False
    assert err_body["error"]["code"] == "PROJECT_LIMIT_REACHED"
    assert "maximum limit of 3" in err_body["error"]["message"]
    assert err_body["error"]["details"]["current_count"] == 3
    assert err_body["error"]["details"]["max_limit"] == 3

    # 4. Existing projects remain fully viewable, editable, and listable
    list_res = client.get("/api/projects", cookies=cookies)
    assert list_res.status_code == 200
    assert list_res.json()["pagination"]["total_count"] == 3

    view_res = client.get(f"/api/projects/{created_ids[0]}", cookies=cookies)
    assert view_res.status_code == 200
    assert view_res.json()["data"]["name"] == "Venture 1"

    edit_res = client.patch(
        f"/api/projects/{created_ids[0]}",
        json={"name": "Venture 1 - Updated Name"},
        cookies=cookies,
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["data"]["name"] == "Venture 1 - Updated Name"


def test_deletion_frees_project_slot(client):
    """Verify that deleting an existing project frees a slot, allowing creation of another project."""
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "delete_slot_user",
            "email": "delete_slot@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    cookies = reg_res.cookies

    # Create 3 projects
    pids = []
    for i in range(1, 4):
        res = client.post(
            "/api/projects",
            json={
                "name": f"Slot Project {i}",
                "industry": "HealthTech",
                "idea_description": f"Description for slot project {i}",
            },
            cookies=cookies,
        )
        assert res.status_code == 201
        pids.append(res.json()["data"]["id"])

    # Attempt 4th project -> rejected
    res_rejected = client.post(
        "/api/projects",
        json={
            "name": "Slot Project 4",
            "industry": "HealthTech",
            "idea_description": "Description for slot project 4",
        },
        cookies=cookies,
    )
    assert res_rejected.status_code == 403

    # Delete project 2
    del_res = client.delete(f"/api/projects/{pids[1]}", cookies=cookies)
    assert del_res.status_code == 200

    # Creating another project should now succeed
    res_freed = client.post(
        "/api/projects",
        json={
            "name": "Slot Project Replacement",
            "industry": "HealthTech",
            "idea_description": "Description for replacement project",
        },
        cookies=cookies,
    )
    assert res_freed.status_code == 201
    assert res_freed.json()["data"]["name"] == "Slot Project Replacement"

    # Now at 3 again -> 4th attempt should be rejected again
    res_capped_again = client.post(
        "/api/projects",
        json={
            "name": "Slot Project Overflow",
            "industry": "HealthTech",
            "idea_description": "Description for overflow project",
        },
        cookies=cookies,
    )
    assert res_capped_again.status_code == 403


def test_separate_users_have_independent_limits(client):
    """Verify that User A reaching 3 projects does not affect User B's ability to create 3 projects."""
    # Register User A
    user_a_res = client.post(
        "/api/auth/register",
        json={
            "username": "user_alpha",
            "email": "alpha@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    cookies_a = user_a_res.cookies

    # Register User B
    user_b_res = client.post(
        "/api/auth/register",
        json={
            "username": "user_beta",
            "email": "beta@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    cookies_b = user_b_res.cookies

    # User A creates 3 projects
    for i in range(1, 4):
        res = client.post(
            "/api/projects",
            json={
                "name": f"Alpha Proj {i}",
                "industry": "CleanTech",
                "idea_description": f"Idea description for Alpha {i}",
            },
            cookies=cookies_a,
        )
        assert res.status_code == 201

    # User A project 4 is rejected
    res_a_4 = client.post(
        "/api/projects",
        json={
            "name": "Alpha Proj 4",
            "industry": "CleanTech",
            "idea_description": "Idea description for Alpha 4",
        },
        cookies=cookies_a,
    )
    assert res_a_4.status_code == 403

    # User B can still create 3 projects without issue
    for i in range(1, 4):
        res = client.post(
            "/api/projects",
            json={
                "name": f"Beta Proj {i}",
                "industry": "CleanTech",
                "idea_description": f"Idea description for Beta {i}",
            },
            cookies=cookies_b,
        )
        assert res.status_code == 201, f"User B project {i} must succeed independently"

    # User B project 4 is also rejected
    res_b_4 = client.post(
        "/api/projects",
        json={
            "name": "Beta Proj 4",
            "industry": "CleanTech",
            "idea_description": "Idea description for Beta 4",
        },
        cookies=cookies_b,
    )
    assert res_b_4.status_code == 403


def test_unauthenticated_project_creation_rejected(client):
    """Verify unauthenticated requests cannot create projects or bypass limit checks."""
    res = client.post(
        "/api/projects",
        json={
            "name": "Anon Project",
            "industry": "Security",
            "idea_description": "Anonymous attempts must fail authentication.",
        },
    )
    assert res.status_code == 401


def test_concurrent_project_creation_respects_cap(tmp_path):
    """Verify that simultaneous creation requests for the same user cannot exceed MAX_PROJECTS_PER_USER."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.core.exceptions import ProjectLimitExceededError
    from app.schemas.project import ProjectCreateRequest

    db_file = tmp_path / "concurrent_projects.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    with engine.connect() as con:
        con.execute(text("PRAGMA journal_mode=WAL;"))
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    init_db = SessionLocal()
    user = User(
        username="concurrent_limit_user",
        email="concurrent_limit@example.com",
        password_hash="fakehash",
        display_name="Concurrent Tester",
    )
    init_db.add(user)
    init_db.commit()
    init_db.refresh(user)
    user_id = user.id
    init_db.close()

    success_count = 0
    failure_count = 0

    def attempt_create(idx: int):
        thread_db = SessionLocal()
        try:
            thread_user = thread_db.get(User, user_id)
            req = ProjectCreateRequest(
                name=f"Concurrent Project {idx}",
                industry="Tech",
                idea_description=f"Concurrent creation test project {idx}",
                business_stage="idea",
            )
            create_project(thread_db, thread_user, req)
            return True, None
        except ProjectLimitExceededError as err:
            return False, str(err)
        except Exception as e:
            return False, f"Unexpected error: {e}"
        finally:
            thread_db.close()

    # Attempt 6 simultaneous creations
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(attempt_create, i) for i in range(6)]
        results = [f.result() for f in futures]
        for ok, msg in results:
            if ok:
                success_count += 1
            else:
                failure_count += 1

    # Exactly MAX_PROJECTS_PER_USER (3) must succeed; the rest must fail
    assert success_count == MAX_PROJECTS_PER_USER, f"Expected exactly {MAX_PROJECTS_PER_USER} successes, got {success_count}. Details: {results}"
    assert failure_count == 3, f"Expected 3 rejections, got {failure_count}"

    # Verify database has exactly 3 projects for this user
    verify_db = SessionLocal()
    final_count = verify_db.query(Project).filter(Project.user_id == user_id).count()
    verify_db.close()
    assert final_count == MAX_PROJECTS_PER_USER
