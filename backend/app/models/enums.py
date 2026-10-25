from enum import Enum


class UserRole(str, Enum):
    """User role enumeration. Use `rank`/`at_least` to compare privilege."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    DEFAULT = "default"

    def __str__(self) -> str:
        return self.value

    @property
    def rank(self) -> int:
        """Privilege level: default < moderator < admin."""
        return _ROLE_RANK[self]

    def at_least(self, other: "UserRole") -> bool:
        """Whether this role has at least the privileges of `other`."""
        return self.rank >= other.rank


_ROLE_RANK = {UserRole.DEFAULT: 0, UserRole.MODERATOR: 1, UserRole.ADMIN: 2}
