from typing import List
from sqlalchemy.orm import Session

from app.models.role_change import RoleChange
from app.repositories.base import BaseRepository


class RoleChangeRepository(BaseRepository[RoleChange]):
    """Repository for RoleChange model."""

    def __init__(self, db: Session):
        """
        Initialize RoleChange repository.

        Args:
            db: Database session
        """
        super().__init__(RoleChange, db)

    def get_for_user(self, user_id: int) -> List[RoleChange]:
        """
        Get a user's role changes, oldest first.

        Args:
            user_id: User ID

        Returns:
            List of RoleChange instances
        """
        return (
            self.db.query(RoleChange)
            .filter(RoleChange.user_id == user_id)
            .order_by(RoleChange.id)
            .all()
        )
