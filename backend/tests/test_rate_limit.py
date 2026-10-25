import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.config import settings
from app.core.client_ip import get_client_ip

LINK = f"{settings.API_V1_PREFIX}/auth/magic-link"


@pytest.fixture
def limits(monkeypatch):
    monkeypatch.setattr(settings, "MAGIC_LINK_RATE_LIMIT_PER_EMAIL", 2)
    monkeypatch.setattr(settings, "MAGIC_LINK_RATE_LIMIT_PER_IP", 3)
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)


def ask(api, email, ip="203.0.113.7"):
    return api.post(LINK, json={"email": email}, headers={"X-Forwarded-For": ip})


def test_per_email_limit_returns_429(api, emails, limits):
    assert ask(api, "spam@example.com").status_code == 200
    assert ask(api, "spam@example.com", ip="198.51.100.1").status_code == 200

    response = ask(api, "spam@example.com", ip="198.51.100.2")
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) == settings.MAGIC_LINK_RATE_LIMIT_WINDOW_MINUTES * 60
    assert len(emails.sent) == 2


def test_per_ip_limit_returns_429(api, emails, limits):
    for n in range(3):
        assert ask(api, f"victim{n}@example.com").status_code == 200
    assert ask(api, "victim3@example.com").status_code == 429
    assert ask(api, "victim3@example.com", ip="198.51.100.9").status_code == 200


def test_failed_sends_do_not_count(api, emails, limits, monkeypatch):
    async def fail(*args, **kwargs):
        return False

    monkeypatch.setattr(emails, "send_magic_link", fail)
    for _ in range(4):  # over both the per-email (2) and per-IP (3) limits
        assert ask(api, "outage@example.com").status_code == 500

    monkeypatch.delattr(emails, "send_magic_link")  # provider is back
    assert ask(api, "outage@example.com").status_code == 200
    assert len(emails.sent) == 1


def test_window_is_configurable(api, emails, limits, monkeypatch):
    monkeypatch.setattr(settings, "MAGIC_LINK_RATE_LIMIT_WINDOW_MINUTES", 0)
    for _ in range(4):
        assert ask(api, "patient@example.com").status_code == 200


@pytest.mark.parametrize(
    "hops, forwarded, expected",
    [
        (1, "203.0.113.7", "203.0.113.7"),
        (1, "1.2.3.4, 203.0.113.7", "203.0.113.7"),  # leftmost entry is forgeable
        (2, "1.2.3.4, 203.0.113.7, 10.0.0.1", "203.0.113.7"),
        (0, "203.0.113.7", "testclient"),
        (1, None, "testclient"),
    ],
)
def test_client_ip(monkeypatch, hops, forwarded, expected):
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", hops)
    probe = FastAPI()

    @probe.get("/ip")
    def ip(client_ip=Depends(get_client_ip)):
        return client_ip

    headers = {"X-Forwarded-For": forwarded} if forwarded else {}
    assert TestClient(probe).get("/ip", headers=headers).json() == expected
