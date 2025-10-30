from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Polito-Log API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Open source project for tracking political accountability"

    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"  # Change in production!
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Magic Link Settings
    MAGIC_LINK_EXPIRE_MINUTES: int = 15  # Magic links expire in 15 minutes
    FRONTEND_URL: str = "http://localhost:5173"  # Frontend URL for magic links

    # Email Settings
    BREVO_API_KEY: Optional[str] = None  # Brevo (Sendinblue) API key for production emails
    BREVO_SENDER_EMAIL: str = "noreply@polito-log.lt"  # Sender email address
    BREVO_SENDER_NAME: str = "Polito-Log"  # Sender name

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
