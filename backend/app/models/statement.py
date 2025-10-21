from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.database import Base


class StatementStatus(str, enum.Enum):
    """Enum for statement verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    RETRACTED = "retracted"


class Statement(Base):
    """SQLAlchemy model for political statements."""

    __tablename__ = "statements"

    id: int = Column(Integer, primary_key=True, index=True)
    politician_name: str = Column(String(255), nullable=False, index=True)
    party: str = Column(String(255), nullable=False, index=True)
    statement_text: str = Column(Text, nullable=False)
    source_url: Optional[str] = Column(String(512), nullable=True)
    statement_date: datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    category: Optional[str] = Column(String(100), nullable=True, index=True)
    status: StatementStatus = Column(
        SQLEnum(StatementStatus),
        default=StatementStatus.PENDING,
        nullable=False,
        index=True
    )
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Statement(id={self.id}, politician={self.politician_name}, party={self.party})>"
