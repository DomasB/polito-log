import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import User
from app.models.enums import UserRole


@pytest.fixture
def db():
    session = SessionLocal()
    created = []
    try:
        yield session, created
    finally:
        session.rollback()
        for user_id in created:
            session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        session.commit()
        session.close()


def _username() -> str:
    return f"role-{uuid.uuid4().hex[:12]}"


@pytest.mark.parametrize("role", list(UserRole))
def test_role_round_trips_by_value(db, role):
    session, created = db
    name = _username()
    user = User(email=f"{name}@example.com", username=name, role=role)
    session.add(user)
    session.commit()
    created.append(user.id)

    stored = session.execute(
        text("SELECT role FROM users WHERE id = :id"), {"id": user.id}
    ).scalar_one()
    assert stored == role.value

    session.expire_all()
    assert session.get(User, user.id).role is role


def test_rows_written_without_role_load_as_default(db):
    # Rows that predate the role column get the server default.
    session, created = db
    name = _username()
    user_id = session.execute(
        text(
            "INSERT INTO users (email, username, is_active)"
            " VALUES (:email, :username, true) RETURNING id"
        ),
        {"email": f"{name}@example.com", "username": name},
    ).scalar_one()
    session.commit()
    created.append(user_id)

    assert session.get(User, user_id).role is UserRole.DEFAULT


def test_unknown_role_is_rejected_by_the_database(db):
    session, _ = db
    name = _username()
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO users (email, username, is_active, role)"
                " VALUES (:email, :username, true, 'DEFAULT')"
            ),
            {"email": f"{name}@example.com", "username": name},
        )
