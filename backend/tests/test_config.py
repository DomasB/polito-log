import pytest
from pydantic import ValidationError

from app.config import Settings

DB_URL = "postgresql://user:pass@localhost:5432/db"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # Settings also reads the process environment (conftest.py sets a JWT key).
    for name in ("ENVIRONMENT", "JWT_SECRET_KEY", "BREVO_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def make_settings(**overrides) -> Settings:
    # _env_file=None keeps a local .env from leaking into the test.
    return Settings(_env_file=None, DATABASE_URL=DB_URL, **overrides)


def test_production_without_secrets_fails():
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY, BREVO_API_KEY"):
        make_settings(ENVIRONMENT="production")


def test_production_with_only_jwt_key_fails_naming_brevo():
    with pytest.raises(ValidationError) as exc:
        make_settings(ENVIRONMENT="production", JWT_SECRET_KEY="real-secret")
    assert "BREVO_API_KEY" in str(exc.value)
    assert "JWT_SECRET_KEY" not in str(exc.value)


def test_production_with_all_secrets_starts():
    settings = make_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="real-secret",
        BREVO_API_KEY="brevo-key",
    )
    assert settings.ENVIRONMENT == "production"


def test_development_starts_without_secrets():
    settings = make_settings(ENVIRONMENT="development")
    assert settings.BREVO_API_KEY is None


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:pass@localhost:5432/db",
        "postgres://user:pass@localhost:5432/db",
        "postgresql+psycopg://user:pass@localhost:5432/db",
    ],
)
def test_database_url_uses_psycopg_driver(url):
    settings = Settings(_env_file=None, DATABASE_URL=url)
    assert settings.DATABASE_URL == "postgresql+psycopg://user:pass@localhost:5432/db"
