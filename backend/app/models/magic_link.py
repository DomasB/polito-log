from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class MagicLink(Base):
    """SQLAlchemy model for magic link authentication tokens."""

    __tablename__ = "magic_links"

    id: int = Column(Integer, primary_key=True, index=True)
    token: str = Column(String(255), unique=True, nullable=False, index=True)
    email: str = Column(String(255), nullable=False, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for new users
    is_used: bool = Column(Boolean, default=False, nullable=False)
    expires_at: datetime = Column(DateTime(timezone=True), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used_at: datetime = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<MagicLink(id={self.id}, email={self.email}, is_used={self.is_used})>"
