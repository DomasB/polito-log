from app.config import settings
from app.core.security import create_access_token
from app.models import User
from app.models.enums import UserRole
from app.services.user import UserService

AUTH = f"{settings.API_V1_PREFIX}/auth"


def login(api, emails, email) -> dict:
    api.post(f"{AUTH}/magic-link", json={"email": email})
    token = api.post(f"{AUTH}/verify", json={"token": emails.last_token()}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_logout_everywhere_revokes_all_sessions(api, emails):
    first = login(api, emails, "multi@example.com")
    second = login(api, emails, "multi@example.com")
    assert api.get(f"{AUTH}/me", headers=first).status_code == 200

    assert api.post(f"{AUTH}/logout-all", headers=second).status_code == 204

    assert api.get(f"{AUTH}/me", headers=first).status_code == 401
    assert api.get(f"{AUTH}/me", headers=second).status_code == 401
    assert api.get(f"{AUTH}/me", headers=login(api, emails, "multi@example.com")).status_code == 200


def test_role_change_revokes_sessions(api, emails, db_session):
    headers = login(api, emails, "demoted@example.com")
    UserService(db_session).grant_role("demoted@example.com", UserRole.ADMIN, changed_by="cli:test")
    assert api.get(f"{AUTH}/me", headers=headers).status_code == 401


def test_token_without_version_is_rejected(api, emails, db_session):
    login(api, emails, "legacy@example.com")
    user = db_session.query(User).filter_by(email="legacy@example.com").one()
    legacy = create_access_token({"sub": str(user.id)})
    response = api.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {legacy}"})
    assert response.status_code == 401
