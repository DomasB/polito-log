from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from urllib.parse import urlsplit

DEFAULT_JWT_SECRET_KEY = "your-secret-key-change-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Polito-Log API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Open source project for tracking political accountability"

    # JWT Settings
    JWT_SECRET_KEY: str = DEFAULT_JWT_SECRET_KEY  # Must be overridden in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Magic Link Settings
    MAGIC_LINK_EXPIRE_MINUTES: int = 15  # Magic links expire in 15 minutes
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for magic links
    # Comma-separated origins allowed by CORS; empty means just FRONTEND_URL's origin
    CORS_ORIGINS: str = ""

    # Magic link rate limits: requests allowed per window, per email and per client IP
    MAGIC_LINK_RATE_LIMIT_WINDOW_MINUTES: int = 60
    MAGIC_LINK_RATE_LIMIT_PER_EMAIL: int = 5
    MAGIC_LINK_RATE_LIMIT_PER_IP: int = 20

    # Number of reverse proxies in front of the app (Railway: 1). The client IP is
    # taken from X-Forwarded-For that many entries from the right; 0 ignores it.
    TRUSTED_PROXY_HOPS: int = 1

    # Email Settings
    BREVO_API_KEY: Optional[str] = None  # Brevo (Sendinblue) API key for production emails
    BREVO_SENDER_EMAIL: str = "noreply@polito-log.lt"  # Sender email address
    BREVO_SENDER_NAME: str = "Polito-Log"  # Sender name

    @field_validator("DATABASE_URL")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        """Point bare postgres URLs (as Railway provides them) at psycopg 3."""
        for scheme in ("postgresql://", "postgres://"):
            if url.startswith(scheme):
                return "postgresql+psycopg://" + url[len(scheme):]
        return url

    @property
    def cors_origins(self) -> list[str]:
        """Origins allowed to call the API from a browser."""
        if self.CORS_ORIGINS.strip():
            return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        parsed = urlsplit(self.FRONTEND_URL)
        return [f"{parsed.scheme}://{parsed.netloc}"]

    @model_validator(mode="after")
    def require_production_secrets(self) -> "Settings":
        """Refuse to start in production with insecure or missing secrets."""
        if self.ENVIRONMENT != "production":
            return self
        missing = []
        if self.JWT_SECRET_KEY == DEFAULT_JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")
        if not self.BREVO_API_KEY:
            missing.append("BREVO_API_KEY")
        if missing:
            raise ValueError(
                f"Production requires these secrets to be set: {', '.join(missing)}"
            )
        return self


settings = Settings()
