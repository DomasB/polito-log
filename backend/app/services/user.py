from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.role_change import RoleChange
from app.models.user import User
from app.repositories.role_change import RoleChangeRepository
from app.repositories.user import UserRepository


class UserNotFoundError(Exception):
    """Raised when no user has the given email."""


class UserService:
    """Service layer for user administration."""

    def __init__(self, db: Session):
        """
        Initialize User service.

        Args:
            db: Database session
        """
        self.user_repository = UserRepository(db)
        self.role_change_repository = RoleChangeRepository(db)

    def grant_role(self, email: str, role: UserRole, changed_by: str) -> User:
        """
        Set a user's role and record the change in the role_changes audit log.
        This is the only way a role changes: there is no HTTP path to it.

        Args:
            email: Email of an existing user
            role: Role to assign
            changed_by: Who is making the change, e.g. "cli:alice"

        Returns:
            Updated User instance

        Raises:
            UserNotFoundError: If no user has this email
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(email)
        if user.role is role:
            return user

        change = RoleChange(
            user_id=user.id,
            old_role=user.role.value,
            new_role=role.value,
            changed_by=changed_by,
        )
        user.role = role
        # One commit for both the role and its audit row
        self.role_change_repository.create(change)
        return user
