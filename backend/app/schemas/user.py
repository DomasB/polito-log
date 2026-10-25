from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.models.enums import UserRole


class UserBase(BaseModel):
    """Base schema for User with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserSelfUpdate(BaseModel):
    """Schema for a user updating their own profile. Only the username can change."""

    username: Optional[str] = Field(None, min_length=3, max_length=100)

    # Anything else (email, is_active, role, ...) is a 422, not silently ignored.
    model_config = ConfigDict(extra="forbid")


class UserInDB(UserBase):
    """Schema for user as stored in database."""

    id: int
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    """Schema for user API responses."""
    pass


class UserPublic(BaseModel):
    """Schema for public user information (limited fields)."""

    # No role: who the moderators and admins are is not public (polito-log-1g4.7).
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    """Schema for the user returned alongside an access token."""

    id: int
    email: EmailStr
    username: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
