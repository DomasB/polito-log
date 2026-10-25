from datetime import datetime, timezone

import pytest

from app.config import settings
from app.models.statement import Statement, StatementStatus

SEARCH = f"{settings.API_V1_PREFIX}/statements/search/"


@pytest.fixture
def statements(db_session):
    texts = ["Taxes up 50% next year", "Taxes up 500 euros", "snake_case_party", "snakeXcase"]
    db_session.add_all(
        Statement(
            politician_name="Wildcard Tester",
            party="Search Party",
            statement_text=text,
            statement_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            # Anonymous searches only see verified statements.
            status=StatementStatus.VERIFIED,
        )
        for text in texts
    )
    db_session.commit()


def search(api, q):
    response = api.get(SEARCH, params={"q": q})
    assert response.status_code == 200
    return sorted(s["statement_text"] for s in response.json())


@pytest.mark.parametrize(
    "q, expected",
    [
        ("50%", ["Taxes up 50% next year"]),
        ("50", ["Taxes up 50% next year", "Taxes up 500 euros"]),
        ("snake_case", ["snake_case_party"]),
        ("%", ["Taxes up 50% next year"]),
        ("\\", []),
    ],
)
def test_search_matches_wildcards_literally(api, statements, q, expected):
    assert search(api, q) == expected
