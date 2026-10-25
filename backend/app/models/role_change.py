from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class RoleChange(Base):
    """SQLAlchemy model for the audit log of user role changes."""

    __tablename__ = "role_changes"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    old_role: str = Column(String(20), nullable=False)
    new_role: str = Column(String(20), nullable=False)
    # Who made the change, e.g. "cli:alice" or, for a future admin endpoint, "user:42"
    changed_by: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<RoleChange(user_id={self.user_id}, {self.old_role} -> {self.new_role})>"
