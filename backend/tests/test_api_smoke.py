import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import DEFAULT_JWT_SECRET_KEY, settings
from app.core.security import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models import User

client = TestClient(app)


@pytest.fixture
def user():
    suffix = uuid.uuid4().hex[:12]
    db = SessionLocal()
    user = User(email=f"smoke-{suffix}@example.com", username=f"smoke-{suffix}")
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        yield user
    finally:
        db.delete(user)
        db.commit()
        db.close()


def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_statements():
    response = client.get(f"{settings.API_V1_PREFIX}/statements/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_me_accepts_token_signed_with_configured_key(user):
    token = create_access_token({"sub": str(user.id), "ver": user.token_version})
    response = client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_me_rejects_token_signed_with_default_key(user):
    # Regression: a token forged with the well-known default key must not
    # authenticate once a real key is configured.
    assert settings.JWT_SECRET_KEY != DEFAULT_JWT_SECRET_KEY
    forged = jwt.encode(
        {
            "sub": str(user.id),
            "ver": user.token_version,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        DEFAULT_JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401
