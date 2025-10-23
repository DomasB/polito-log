from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """Schema for requesting a magic link."""

    email: EmailStr = Field(..., description="Email address to send magic link to")


class MagicLinkResponse(BaseModel):
    """Schema for magic link request response."""

    message: str = Field(..., description="Response message")
    email: str = Field(..., description="Email address the link was sent to")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration time")
    user: dict = Field(..., description="User information")


class TokenVerify(BaseModel):
    """Schema for verifying a magic link token."""

    token: str = Field(..., description="Magic link token to verify")
