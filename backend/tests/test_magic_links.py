import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.config import settings
from app.core.security import hash_magic_link_token
from app.database import SessionLocal
from app.models import MagicLink, User
from app.repositories.magic_link import MagicLinkRepository

AUTH = f"{settings.API_V1_PREFIX}/auth"


def request_link(api, emails, email) -> str:
    assert api.post(f"{AUTH}/magic-link", json={"email": email}).status_code == 200
    return emails.last_token()


def verify(api, token):
    return api.post(f"{AUTH}/verify", json={"token": token})


def test_token_is_stored_hashed(api, emails, db_session):
    token = request_link(api, emails, "hashed@example.com")
    link = db_session.query(MagicLink).filter_by(email="hashed@example.com").one()
    assert link.token_hash == hash_magic_link_token(token)
    assert token not in link.token_hash


def test_link_works_once(api, emails):
    token = request_link(api, emails, "once@example.com")
    assert verify(api, token).status_code == 200
    assert verify(api, token).status_code == 401


def test_using_a_link_invalidates_the_others(api, emails):
    older = request_link(api, emails, "siblings@example.com")
    newer = request_link(api, emails, "siblings@example.com")
    assert verify(api, newer).status_code == 200
    assert verify(api, older).status_code == 401


def test_expired_link_is_rejected(api, emails, db_session):
    token = request_link(api, emails, "late@example.com")
    db_session.query(MagicLink).filter_by(email="late@example.com").update(
        {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}
    )
    db_session.commit()
    assert verify(api, token).status_code == 401


# The tests below need committed rows visible to several connections, so they
# use real sessions and clean up after themselves.

@pytest.fixture
def committed_links():
    email = f"race-{uuid.uuid4().hex[:12]}@example.com"
    tokens = [uuid.uuid4().hex + uuid.uuid4().hex for _ in range(2)]
    with SessionLocal() as db:
        for token in tokens:
            db.add(MagicLink(
                token_hash=hash_magic_link_token(token),
                email=email,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            ))
        db.commit()
    try:
        yield email, tokens
    finally:
        with SessionLocal() as db:
            db.execute(text("DELETE FROM magic_links WHERE email = :e"), {"e": email})
            db.execute(text("DELETE FROM users WHERE email = :e"), {"e": email})
            db.commit()


def test_consume_waits_for_a_concurrent_consume_and_then_fails(committed_links):
    email, tokens = committed_links
    holder = SessionLocal()
    try:
        # Transaction A uses the first link but has not committed yet.
        holder.execute(
            text("UPDATE magic_links SET is_used = true WHERE email = :e"), {"e": email}
        )

        result = {}
        def consume_second():
            with SessionLocal() as db:
                result["email"] = MagicLinkRepository(db).consume(hash_magic_link_token(tokens[1]))

        racer = threading.Thread(target=consume_second)
        racer.start()
        racer.join(timeout=1)
        assert racer.is_alive(), "consume should block on A's row locks"

        holder.commit()
        racer.join(timeout=5)
        assert result == {"email": None}
    finally:
        holder.close()


def test_concurrent_verifies_yield_one_session(committed_links):
    from app.services.auth import AuthService

    email, tokens = committed_links
    attempts = [tokens[0]] * 4 + [tokens[1]] * 4
    barrier = threading.Barrier(len(attempts))
    results = []

    def attempt(token):
        with SessionLocal() as db:
            barrier.wait()
            results.append(AuthService(db, email_sender=None).verify_magic_link(token))

    threads = [threading.Thread(target=attempt, args=(t,)) for t in attempts]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert sum(result is not None for result in results) == 1
    with SessionLocal() as db:
        assert db.query(User).filter_by(email=email).count() == 1
