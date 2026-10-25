from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app

client = TestClient(app)


def test_responses_send_no_referrer():
    assert client.get("/").headers["Referrer-Policy"] == "no-referrer"


def test_cors_allows_only_the_frontend_origin():
    frontend = settings.cors_origins[0]
    preflight = {"Access-Control-Request-Method": "POST"}

    allowed = client.options("/", headers={"Origin": frontend, **preflight})
    assert allowed.headers.get("access-control-allow-origin") == frontend

    denied = client.options("/", headers={"Origin": "https://evil.example", **preflight})
    assert "access-control-allow-origin" not in denied.headers


def test_cors_origins_setting():
    base = dict(DATABASE_URL="postgresql://x/y")
    assert Settings(**base, FRONTEND_URL="https://polito-log.lt/").cors_origins == ["https://polito-log.lt"]
    assert Settings(**base, CORS_ORIGINS="https://a.lt, https://b.lt/").cors_origins == [
        "https://a.lt", "https://b.lt"
    ]
