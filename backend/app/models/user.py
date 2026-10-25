from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func

from app.database import Base
from app.models.enums import UserRole


class User(Base):
    """SQLAlchemy model for users."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    username: str = Column(String(100), unique=True, nullable=False, index=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    # Stored by value ('admin', not 'ADMIN') and guarded by a CHECK constraint.
    role: UserRole = Column(
        SQLAlchemyEnum(
            UserRole,
            name="user_role",
            native_enum=False,
            length=20,
            create_constraint=True,
            values_callable=lambda roles: [role.value for role in roles],
        ),
        default=UserRole.DEFAULT,
        server_default=UserRole.DEFAULT.value,
        nullable=False
    )
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
