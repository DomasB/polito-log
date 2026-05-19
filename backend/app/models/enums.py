from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    DEFAULT = "default"

    def __str__(self) -> str:
        return self.value
