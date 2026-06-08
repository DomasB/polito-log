from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.magic_link import MagicLink
from app.repositories.base import BaseRepository


class MagicLinkRepository(BaseRepository[MagicLink]):
    """Repository for MagicLink model."""

    def __init__(self, db: Session):
        """
        Initialize MagicLink repository.

        Args:
            db: Database session
        """
        super().__init__(MagicLink, db)

    def get_by_token(self, token: str) -> Optional[MagicLink]:
        """
        Get magic link by token.

        Args:
            token: Magic link token

        Returns:
            MagicLink instance or None if not found
        """
        return self.db.query(MagicLink).filter(MagicLink.token == token).first()

    def get_valid_by_token(self, token: str) -> Optional[MagicLink]:
        """
        Get valid (unused and not expired) magic link by token.

        Args:
            token: Magic link token

        Returns:
            MagicLink instance or None if not found or invalid
        """
        now = datetime.utcnow()
        return (
            self.db.query(MagicLink)
            .filter(
                MagicLink.token == token,
                MagicLink.is_used == False,
                MagicLink.expires_at > now
            )
            .first()
        )

    def mark_as_used(self, magic_link: MagicLink) -> MagicLink:
        """
        Mark a magic link as used.

        Args:
            magic_link: MagicLink instance to mark as used

        Returns:
            Updated MagicLink instance
        """
        magic_link.is_used = True
        magic_link.used_at = datetime.utcnow()
        return self.update(magic_link)

    def cleanup_expired(self) -> int:
        """
        Delete expired magic links.

        Returns:
            Number of deleted records
        """
        now = datetime.utcnow()
        deleted = (
            self.db.query(MagicLink)
            .filter(MagicLink.expires_at < now)
            .delete()
        )
        self.db.commit()
        return deleted
