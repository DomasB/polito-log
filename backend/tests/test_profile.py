import pytest

from app.config import settings
from app.core.usernames import is_reserved_username

AUTH = f"{settings.API_V1_PREFIX}/auth"


def login(api, emails, email) -> tuple[dict, dict]:
    api.post(f"{AUTH}/magic-link", json={"email": email})
    body = api.post(f"{AUTH}/verify", json={"token": emails.last_token()}).json()
    return body["user"], {"Authorization": f"Bearer {body['access_token']}"}


@pytest.mark.parametrize(
    "field", [{"role": "admin"}, {"email": "other@example.com"}, {"is_active": False}]
)
def test_put_me_rejects_fields_other_than_username(api, emails, field):
    _, headers = login(api, emails, "selfupdate@example.com")
    response = api.put(f"{AUTH}/me", json={"username": "selfupdate2", **field}, headers=headers)
    assert response.status_code == 422

    me = api.get(f"{AUTH}/me", headers=headers).json()
    assert (me["username"], me["role"], me["email"], me["is_active"]) == (
        "selfupdate", "default", "selfupdate@example.com", True
    )


def test_put_me_changes_username(api, emails):
    _, headers = login(api, emails, "renamer@example.com")
    response = api.put(f"{AUTH}/me", json={"username": "renamed-user"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "renamed-user"


@pytest.mark.parametrize("username", ["admin", "Moderator", "polito_log", "Admin_1", "support"])
def test_put_me_rejects_reserved_username(api, emails, username):
    _, headers = login(api, emails, "wannabe@example.com")
    response = api.put(f"{AUTH}/me", json={"username": username}, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username is reserved"


def test_signup_does_not_derive_a_reserved_username(api, emails):
    user, _ = login(api, emails, "admin@example.com")
    assert not is_reserved_username(user["username"])


@pytest.mark.parametrize(
    "username, reserved",
    [
        ("admin", True),
        ("a.d.m.i.n", True),
        ("administratorius", True),
        ("MOD", True),
        ("staff", True),
        ("modestas", False),
        ("jonas", False),
        ("team-player", False),
    ],
)
def test_is_reserved_username(username, reserved):
    assert is_reserved_username(username) is reserved
