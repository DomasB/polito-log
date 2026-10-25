"""Statement search filters, status visibility and status write permissions."""
import uuid
from datetime import UTC, datetime

import pytest

from app.config import settings
from app.core.security import create_access_token
from app.models import Statement, User
from app.models.enums import UserRole
from app.models.statement import StatementStatus

BASE = f"{settings.API_V1_PREFIX}/statements"
SEARCH = f"{BASE}/search/"


@pytest.fixture
def make_user(db_session):
    def make(role: UserRole) -> User:
        name = f"sf-{uuid.uuid4().hex[:12]}"
        user = User(email=f"{name}@example.com", username=name, role=role)
        db_session.add(user)
        db_session.commit()
        return user

    return make


def auth(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "ver": user.token_version})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewers(make_user):
    """Request headers per kind of viewer."""
    return {
        "anonymous": {},
        "default": auth(make_user(UserRole.DEFAULT)),
        "moderator": auth(make_user(UserRole.MODERATOR)),
        "admin": auth(make_user(UserRole.ADMIN)),
    }


@pytest.fixture
def tag():
    """Unique marker so tests ignore rows already in the dev database."""
    return f"zq{uuid.uuid4().hex[:10]}"


@pytest.fixture
def corpus(db_session, tag):
    """One statement per status, plus rows for the text matchers."""
    rows = [
        # (key, politician, party, category, status)
        ("pending", "Ona Pending", "LSDP", "economy", StatementStatus.PENDING),
        ("verified", "Jonas Verified", "LSDP", "economy", StatementStatus.VERIFIED),
        ("disputed", "Rasa Disputed", "TS-LKD", "health", StatementStatus.DISPUTED),
        ("retracted", "Petras Retracted", "TS-LKD", "health", StatementStatus.RETRACTED),
        ("rejected", "Ieva Rejected", "LSDPR", "defence", StatementStatus.REJECTED),
        ("v_lsdpr", "Mantas Verified", "lsdpr", "economy", StatementStatus.VERIFIED),
        ("v_pct", "Pct Verified", "100% Party", "eco_nomy", StatementStatus.VERIFIED),
        ("v_plain", "Plain Verified", "1000 Party", "ecoXnomy", StatementStatus.VERIFIED),
    ]
    statements = {}
    for key, politician, party, category, status in rows:
        statement = Statement(
            politician_name=f"{politician} {tag}",
            party=party,
            category=category,
            statement_text=f"{key} {tag}",
            statement_date=datetime(2026, 1, 1, tzinfo=UTC),
            status=status,
        )
        db_session.add(statement)
        statements[key] = statement
    db_session.commit()
    return statements


def keys(response, tag) -> list[str]:
    """Statement keys (first word of the text) of this test's rows in a response."""
    assert response.status_code == 200, response.text
    return sorted(
        s["statement_text"].split()[0] for s in response.json() if tag in s["statement_text"]
    )


def search(api, headers, tag, **params):
    params = {"q": tag, "limit": 500, **params}
    return keys(api.get(SEARCH, params=params, headers=headers), tag)


ALL = ["disputed", "pending", "rejected", "retracted", "v_lsdpr", "v_pct", "v_plain", "verified"]
VERIFIED = ["v_lsdpr", "v_pct", "v_plain", "verified"]


# --- Visibility -------------------------------------------------------------


@pytest.mark.parametrize(
    "viewer, expected",
    [("anonymous", VERIFIED), ("default", VERIFIED), ("moderator", ALL), ("admin", ALL)],
)
def test_list_visibility(api, corpus, viewers, tag, viewer, expected):
    response = api.get(f"{BASE}/", params={"limit": 500}, headers=viewers[viewer])
    assert keys(response, tag) == expected


@pytest.mark.parametrize(
    "viewer, expected",
    [("anonymous", VERIFIED), ("default", VERIFIED), ("moderator", ALL), ("admin", ALL)],
)
def test_search_visibility(api, corpus, viewers, tag, viewer, expected):
    assert search(api, viewers[viewer], tag) == expected


@pytest.mark.parametrize(
    "viewer, expected",
    [("anonymous", []), ("default", []), ("moderator", ["pending"])],
)
def test_politician_endpoint_visibility(api, corpus, viewers, tag, viewer, expected):
    response = api.get(f"{BASE}/politician/Ona Pending {tag}", headers=viewers[viewer])
    assert keys(response, tag) == expected


@pytest.mark.parametrize(
    "viewer, expected",
    [
        ("anonymous", ["verified"]),
        ("default", ["verified"]),
        ("moderator", ["pending", "verified"]),
    ],
)
def test_party_endpoint_visibility(api, corpus, viewers, tag, viewer, expected):
    response = api.get(f"{BASE}/party/LSDP", params={"limit": 500}, headers=viewers[viewer])
    assert keys(response, tag) == expected


@pytest.mark.parametrize("viewer", ["anonymous", "default"])
def test_status_endpoint_forbids_non_verified_for_non_moderators(api, corpus, viewers, viewer):
    response = api.get(f"{BASE}/status/pending", headers=viewers[viewer])
    assert response.status_code == 403


@pytest.mark.parametrize("viewer", ["anonymous", "default"])
def test_status_endpoint_allows_verified_for_everyone(api, corpus, viewers, tag, viewer):
    response = api.get(f"{BASE}/status/verified", params={"limit": 500}, headers=viewers[viewer])
    assert keys(response, tag) == VERIFIED


def test_status_endpoint_allows_any_status_for_moderators(api, corpus, viewers, tag):
    response = api.get(
        f"{BASE}/status/rejected", params={"limit": 500}, headers=viewers["moderator"]
    )
    assert keys(response, tag) == ["rejected"]


def test_get_by_id_returns_rejected_statement_to_anonymous(api, corpus):
    response = api.get(f"{BASE}/{corpus['rejected'].id}")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.parametrize("viewer", ["anonymous", "default"])
@pytest.mark.parametrize("param", ["status", "status_not"])
def test_status_filters_forbidden_for_non_moderators(api, corpus, viewers, viewer, param):
    response = api.get(SEARCH, params={param: "verified"}, headers=viewers[viewer])
    assert response.status_code == 403
    assert param in response.json()["detail"]


# --- Status IN / NOT IN -----------------------------------------------------


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"status": "pending"}, ["pending"]),
        ({"status": ["pending", "rejected"]}, ["pending", "rejected"]),
        ({"status_not": "verified"}, ["disputed", "pending", "rejected", "retracted"]),
        ({"status_not": ["verified", "pending", "rejected"]}, ["disputed", "retracted"]),
        ({"status": ["pending", "disputed"], "status_not": "disputed"}, ["pending"]),
    ],
)
def test_status_in_and_not_in(api, corpus, viewers, tag, params, expected):
    assert search(api, viewers["moderator"], tag, **params) == expected


def test_invalid_status_value_is_rejected(api, viewers):
    response = api.get(SEARCH, params={"status": "bogus"}, headers=viewers["moderator"])
    assert response.status_code == 422


# --- Text matchers ----------------------------------------------------------


@pytest.mark.parametrize(
    "params, expected",
    [
        # Unquoted: case-insensitive contains.
        ({"party": "lsdp"}, ["pending", "rejected", "v_lsdpr", "verified"]),
        # Quoted: case-insensitive exact equality.
        ({"party": '"lsdp"'}, ["pending", "verified"]),
        ({"party": '"LSDPR"'}, ["rejected", "v_lsdpr"]),
        # Repeated values OR together.
        ({"party": ['"LSDP"', '"ts-lkd"']}, ["disputed", "pending", "retracted", "verified"]),
        ({"politician": "VERIFIED"}, ["v_lsdpr", "v_pct", "v_plain", "verified"]),
        ({"politician": ["ona p", "IEVA"]}, ["pending", "rejected"]),
        ({"category": "HEALTH"}, ["disputed", "retracted"]),
        ({"category": '"Economy"'}, ["pending", "v_lsdpr", "verified"]),
        ({"category": "econ"}, ["pending", "v_lsdpr", "verified"]),
    ],
)
def test_text_matchers(api, corpus, viewers, tag, params, expected):
    assert search(api, viewers["moderator"], tag, **params) == expected


def test_quoted_politician_matches_whole_name(api, corpus, viewers, tag):
    params = {"politician": f'"ona pending {tag.upper()}"'}
    assert search(api, viewers["moderator"], tag, **params) == ["pending"]
    params = {"politician": '"ona pending"'}
    assert search(api, viewers["moderator"], tag, **params) == []


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"party": "100%"}, ["v_pct"]),
        ({"party": "100"}, ["v_pct", "v_plain"]),
        ({"party": '"100% party"'}, ["v_pct"]),
        ({"party": '"100_ party"'}, []),
        ({"category": "eco_nomy"}, ["v_pct"]),
        ({"category": '"eco_nomy"'}, ["v_pct"]),
        ({"politician": "%"}, []),
    ],
)
def test_text_matchers_escape_wildcards(api, corpus, viewers, tag, params, expected):
    assert search(api, viewers["moderator"], tag, **params) == expected


# --- Combination ------------------------------------------------------------


def test_params_and_together(api, corpus, viewers, tag):
    params = {"party": "lsdp", "category": '"economy"', "status_not": "pending"}
    assert search(api, viewers["moderator"], tag, **params) == ["v_lsdpr", "verified"]


def test_non_moderator_filters_are_limited_to_verified(api, corpus, viewers, tag):
    assert search(api, viewers["default"], tag, party="lsdp") == ["v_lsdpr", "verified"]


def test_q_is_optional(api, corpus, viewers, tag):
    response = api.get(
        SEARCH, params={"politician": tag, "limit": 500}, headers=viewers["moderator"]
    )
    assert keys(response, tag) == ALL
    response = api.get(SEARCH, params={"limit": 500})
    assert keys(response, tag) == VERIFIED


# --- Writes -----------------------------------------------------------------


def new_statement(tag, status="verified") -> dict:
    return {
        "politician_name": f"Writer {tag}",
        "party": "Write Party",
        "statement_text": f"written {tag}",
        "statement_date": "2026-01-01T00:00:00Z",
        "status": status,
    }


def test_create_forces_pending_for_default_user(api, viewers, tag):
    response = api.post(f"{BASE}/", json=new_statement(tag), headers=viewers["default"])
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


@pytest.mark.parametrize("viewer", ["moderator", "admin"])
def test_create_keeps_status_for_moderators(api, viewers, tag, viewer):
    response = api.post(f"{BASE}/", json=new_statement(tag), headers=viewers[viewer])
    assert response.status_code == 201
    assert response.json()["status"] == "verified"


def test_update_status_forbidden_for_default_user(api, corpus, viewers):
    statement = corpus["pending"]
    response = api.put(
        f"{BASE}/{statement.id}", json={"status": "verified"}, headers=viewers["default"]
    )
    assert response.status_code == 403
    assert "status" in response.json()["detail"]
    assert api.get(f"{BASE}/{statement.id}").json()["status"] == "pending"


def test_update_other_fields_allowed_for_default_user(api, corpus, viewers):
    statement = corpus["pending"]
    response = api.put(
        f"{BASE}/{statement.id}", json={"category": "edited"}, headers=viewers["default"]
    )
    assert response.status_code == 200
    assert response.json()["category"] == "edited"


@pytest.mark.parametrize("viewer", ["moderator", "admin"])
def test_update_status_allowed_for_moderators(api, corpus, viewers, viewer):
    statement = corpus["pending"]
    response = api.put(
        f"{BASE}/{statement.id}", json={"status": "rejected"}, headers=viewers[viewer]
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
