from datetime import datetime
from typing import List, Optional
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


TEXT_MATCH_RULE = (
    "Repeat the parameter to match any of several values (OR). An unquoted value "
    "matches as a case-insensitive substring (`%` and `_` are literal); a value "
    'wrapped in double quotes, e.g. `"LSDP"`, matches the whole field exactly, '
    "case-insensitively."
)


class StatementSearchFilters(BaseModel):
    """Filters for statement search. Every given filter must match (AND)."""

    q: Optional[str] = Field(
        None,
        min_length=1,
        description=(
            "Free text, matched as a case-insensitive substring of the statement text, "
            "politician name or party (`%` and `_` are literal). Optional."
        ),
    )
    status: Optional[List[StatementStatus]] = Field(
        None,
        description=(
            "Only statements with one of these statuses (repeatable; OR / IN). "
            "Moderators and admins only."
        ),
    )
    status_not: Optional[List[StatementStatus]] = Field(
        None,
        description=(
            "Exclude statements with any of these statuses (repeatable; NOT IN). "
            "Moderators and admins only."
        ),
    )
    politician: Optional[List[str]] = Field(
        None, description=f"Politician name filter. {TEXT_MATCH_RULE}"
    )
    party: Optional[List[str]] = Field(None, description=f"Party filter. {TEXT_MATCH_RULE}")
    category: Optional[List[str]] = Field(
        None, description=f"Category filter. {TEXT_MATCH_RULE}"
    )


class StatementSearchQuery(StatementSearchFilters):
    """Query parameters of the search endpoint: filters plus paging. Unknown keys are rejected."""

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of records to return")

    model_config = ConfigDict(extra="forbid")
