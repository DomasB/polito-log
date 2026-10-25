import contextlib
import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import app.cli
from app.core.dependencies import require_role
from app.core.security import create_access_token
from app.database import get_db
from app.models import RoleChange, User
from app.models.enums import UserRole
from app.repositories.role_change import RoleChangeRepository
from app.services.user import UserService


@pytest.fixture
def client(db_session):
    probe = FastAPI()

    @probe.get("/moderation", dependencies=[Depends(require_role(UserRole.MODERATOR))])
    def moderation():
        return {"ok": True}

    probe.dependency_overrides[get_db] = lambda: db_session
    return TestClient(probe)


@pytest.fixture
def make_user(db_session):
    def make(role: UserRole) -> User:
        name = f"rr-{uuid.uuid4().hex[:12]}"
        user = User(email=f"{name}@example.com", username=name, role=role)
        db_session.add(user)
        db_session.commit()
        return user

    return make


def auth(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}


def test_role_order():
    assert UserRole.ADMIN.at_least(UserRole.MODERATOR)
    assert UserRole.MODERATOR.at_least(UserRole.MODERATOR)
    assert not UserRole.DEFAULT.at_least(UserRole.MODERATOR)
    assert not UserRole.MODERATOR.at_least(UserRole.ADMIN)


def test_require_role_rejects_anonymous_with_401(client):
    assert client.get("/moderation").status_code == 401
    bad = {"Authorization": "Bearer not-a-jwt"}
    assert client.get("/moderation", headers=bad).status_code == 401


def test_require_role_rejects_lower_role_with_403(client, make_user):
    response = client.get("/moderation", headers=auth(make_user(UserRole.DEFAULT)))
    assert response.status_code == 403


@pytest.mark.parametrize("role", [UserRole.MODERATOR, UserRole.ADMIN])
def test_require_role_admits_equal_or_higher_role(client, make_user, role):
    response = client.get("/moderation", headers=auth(make_user(role)))
    assert response.status_code == 200


def test_require_role_reads_role_from_database_not_token(client, make_user, db_session):
    user = make_user(UserRole.ADMIN)
    headers = auth(user)
    user.role = UserRole.DEFAULT
    db_session.commit()
    assert client.get("/moderation", headers=headers).status_code == 403


def test_grant_role_writes_audit_row(make_user, db_session):
    user = make_user(UserRole.DEFAULT)
    UserService(db_session).grant_role(user.email, UserRole.ADMIN, changed_by="cli:test")

    [change] = RoleChangeRepository(db_session).get_for_user(user.id)
    assert (change.old_role, change.new_role, change.changed_by) == ("default", "admin", "cli:test")


def test_grant_role_to_current_role_writes_nothing(make_user, db_session):
    user = make_user(UserRole.MODERATOR)
    UserService(db_session).grant_role(user.email, UserRole.MODERATOR, changed_by="cli:test")
    assert RoleChangeRepository(db_session).get_for_user(user.id) == []


def test_cli_grant_role_records_who(make_user, db_session, monkeypatch):
    user = make_user(UserRole.DEFAULT)
    monkeypatch.setattr(app.cli, "SessionLocal", lambda: contextlib.nullcontext(db_session))

    assert app.cli.main(["grant-role", user.email, "moderator", "--by", "alice"]) == 0

    db_session.refresh(user)
    assert user.role is UserRole.MODERATOR
    change = db_session.query(RoleChange).filter_by(user_id=user.id).one()
    assert change.changed_by == "cli:alice"
