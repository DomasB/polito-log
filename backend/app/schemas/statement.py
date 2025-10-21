from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.statement import StatementStatus


class StatementBase(BaseModel):
    """Base schema for Statement with common fields."""

    politician_name: str = Field(..., min_length=1, max_length=255, description="Name of the politician")
    party: str = Field(..., min_length=1, max_length=255, description="Political party")
    statement_text: str = Field(..., min_length=1, description="The actual statement text")
    source_url: Optional[str] = Field(None, max_length=512, description="URL source of the statement")
    statement_date: datetime = Field(..., description="Date when the statement was made")
    category: Optional[str] = Field(None, max_length=100, description="Category of the statement")
    status: StatementStatus = Field(default=StatementStatus.PENDING, description="Verification status")


class StatementCreate(StatementBase):
    """Schema for creating a new statement."""
    pass


class StatementUpdate(BaseModel):
    """Schema for updating an existing statement. All fields are optional."""

    politician_name: Optional[str] = Field(None, min_length=1, max_length=255)
    party: Optional[str] = Field(None, min_length=1, max_length=255)
    statement_text: Optional[str] = Field(None, min_length=1)
    source_url: Optional[str] = Field(None, max_length=512)
    statement_date: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=100)
    status: Optional[StatementStatus] = None
    is_active: Optional[bool] = None


class StatementInDB(StatementBase):
    """Schema for statement as stored in database."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatementResponse(StatementInDB):
    """Schema for statement API responses."""
    pass
