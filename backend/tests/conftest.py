import os

# app.config builds Settings at import time, so the test key must be set before
# any app module is imported. It differs from DEFAULT_JWT_SECRET_KEY on purpose.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-at-least-32-bytes")

from typing import Optional
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_email_sender
from app.core.email import EmailSender
from app.database import engine, get_db
from app.main import app


class RecordingEmailSender(EmailSender):
    """Email sender that keeps the magic links it was asked to send."""

    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    async def send_magic_link(
        self, to_email: str, magic_link: str, username: Optional[str] = None
    ) -> bool:
        self.sent.append((to_email, magic_link))
        return True

    def last_token(self) -> str:
        return parse_qs(urlparse(self.sent[-1][1]).query)["token"][0]


@pytest.fixture
def db_session():
    """A session whose work, commits included, is rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def emails():
    return RecordingEmailSender()


@pytest.fixture
def api(db_session, emails):
    """TestClient whose requests run inside db_session and record sent emails."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_email_sender] = lambda: emails
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
