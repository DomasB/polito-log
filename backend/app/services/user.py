from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
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

    def grant_role(self, email: str, role: UserRole) -> User:
        """
        Set a user's role. The only way a role changes: there is no HTTP path.

        Args:
            email: Email of an existing user
            role: Role to assign

        Returns:
            Updated User instance

        Raises:
            UserNotFoundError: If no user has this email
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(email)
        user.role = role
        return self.user_repository.update(user)
