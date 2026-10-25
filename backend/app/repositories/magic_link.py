from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import func, select, update
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

    def consume(self, token_hash: str) -> Optional[str]:
        """
        Atomically use a valid (unused, unexpired) magic link and invalidate
        every other outstanding link for the same email.

        This is a single UPDATE, so of two concurrent calls (same token, or two
        links for one email) at most one succeeds: the second waits on the
        first's row locks and then finds the rows already used.

        Args:
            token_hash: Hash of the token from the link

        Returns:
            Email the link was issued to, or None if the link is not valid
        """
        valid_link_email = (
            select(MagicLink.email)
            .where(
                MagicLink.token_hash == token_hash,
                MagicLink.is_used.is_(False),
                MagicLink.expires_at > func.now(),
            )
            .scalar_subquery()
        )
        used = self.db.execute(
            update(MagicLink)
            .where(MagicLink.email == valid_link_email, MagicLink.is_used.is_(False))
            .values(is_used=True, used_at=func.now())
            .returning(MagicLink.token_hash, MagicLink.email)
            .execution_options(synchronize_session=False)
        ).all()
        self.db.commit()

        # If another request consumed the link first, it is not among the rows.
        return next((email for hash_, email in used if hash_ == token_hash), None)

    def count_created_since(
        self,
        since: datetime,
        email: Optional[str] = None,
        request_ip: Optional[str] = None
    ) -> int:
        """
        Count magic links created since a point in time.

        Args:
            since: Start of the window
            email: Only count links for this email (optional)
            request_ip: Only count links requested from this IP (optional)

        Returns:
            Number of links
        """
        query = self.db.query(MagicLink).filter(MagicLink.created_at >= since)
        if email is not None:
            query = query.filter(MagicLink.email == email)
        if request_ip is not None:
            query = query.filter(MagicLink.request_ip == request_ip)
        return query.count()

    def cleanup_expired(self) -> int:
        """
        Delete expired magic links.

        Returns:
            Number of deleted records
        """
        now = datetime.now(timezone.utc)
        deleted = (
            self.db.query(MagicLink)
            .filter(MagicLink.expires_at < now)
            .delete()
        )
        self.db.commit()
        return deleted
