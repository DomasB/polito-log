from sqlalchemy import text

from app.cli import main as cli
from app.config import settings
from app.models import User
from app.models.enums import UserRole
from app.services.user import UserService

AUTH = f"{settings.API_V1_PREFIX}/auth"


def login(api, emails, email):
    assert api.post(f"{AUTH}/magic-link", json={"email": email}).status_code == 200
    response = api.post(f"{AUTH}/verify", json={"token": emails.last_token()})
    assert response.status_code == 200
    return response.json()


def test_first_signup_on_empty_database_gets_default_role(api, emails, db_session):
    db_session.execute(text("DELETE FROM magic_links"))
    db_session.execute(text("DELETE FROM users"))

    body = login(api, emails, "first@example.com")

    assert body["user"]["role"] == "default"
    assert db_session.query(User).one().role is UserRole.DEFAULT


def test_profile_update_cannot_grant_a_role(api, emails):
    token = login(api, emails, "climber@example.com")["access_token"]
    response = api.put(
        f"{AUTH}/me",
        json={"username": "climber", "role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.json().get("role") != "admin"


def test_grant_role_sets_the_role(api, emails, db_session):
    login(api, emails, "promoted@example.com")

    UserService(db_session).grant_role("promoted@example.com", UserRole.MODERATOR)

    user = db_session.query(User).filter_by(email="promoted@example.com").one()
    assert user.role is UserRole.MODERATOR


def test_cli_grant_role_rejects_unknown_email(capsys):
    assert cli(["grant-role", "nobody-here@example.com", "admin"]) == 1
    assert "must log in once" in capsys.readouterr().err
