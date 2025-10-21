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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
