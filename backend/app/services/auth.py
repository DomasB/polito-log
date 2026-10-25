from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.repositories.user import UserRepository
from app.repositories.magic_link import MagicLinkRepository
from app.models.user import User
from app.models.magic_link import MagicLink
from app.schemas.user import UserCreate
from app.core.security import (
    create_access_token,
    generate_magic_link_token,
    hash_magic_link_token,
)
from app.core.email import EmailSender
from app.core.usernames import is_reserved_username
from app.config import settings


class UsernameUnavailableError(Exception):
    """Raised when a requested username is reserved or already taken."""


class RateLimitExceededError(Exception):
    """Raised when too many magic links were requested recently."""

    def __init__(self, retry_after_seconds: int):
        super().__init__("Too many magic link requests, try again later")
        self.retry_after_seconds = retry_after_seconds


class AuthService:
    """Service layer for authentication business logic."""

    def __init__(self, db: Session, email_sender: EmailSender):
        """
        Initialize Auth service.

        Args:
            db: Database session
            email_sender: Email sender implementation
        """
        self.user_repository = UserRepository(db)
        self.magic_link_repository = MagicLinkRepository(db)
        self.email_sender = email_sender
        self.db = db

    async def request_magic_link(
        self,
        email: str,
        client_ip: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Request a magic link for authentication.
        Creates a new user if email doesn't exist.

        Args:
            email: Email address to send magic link to
            client_ip: IP address of the requester, for rate limiting

        Returns:
            Tuple of (success: bool, message: str)

        Raises:
            RateLimitExceededError: If the email or IP requested too many links
                within MAGIC_LINK_RATE_LIMIT_WINDOW_MINUTES
        """
        self._check_rate_limit(email, client_ip)

        # Check if user exists
        user = self.user_repository.get_by_email(email)

        # Generate secure token
        token = generate_magic_link_token()

        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )

        # Create magic link record; only the token's hash is stored
        magic_link = MagicLink(
            token_hash=hash_magic_link_token(token),
            email=email,
            user_id=user.id if user else None,
            request_ip=client_ip,
            expires_at=expires_at
        )
        self.magic_link_repository.create(magic_link)

        # Create magic link URL
        # For API-only backend, we'll use a frontend URL with the token
        magic_link_url = f"{settings.FRONTEND_URL}/auth/verify?token={token}"

        # Send email
        username = user.username if user else None
        success = await self.email_sender.send_magic_link(
            to_email=email,
            magic_link=magic_link_url,
            username=username
        )

        if success:
            return True, "Magic link sent successfully"
        else:
            return False, "Failed to send magic link"

    def _check_rate_limit(self, email: str, client_ip: Optional[str]) -> None:
        """Raise RateLimitExceededError if this email or IP is over its limit."""
        window = timedelta(minutes=settings.MAGIC_LINK_RATE_LIMIT_WINDOW_MINUTES)
        since = datetime.now(timezone.utc) - window
        over_email = self.magic_link_repository.count_created_since(
            since, email=email
        ) >= settings.MAGIC_LINK_RATE_LIMIT_PER_EMAIL
        over_ip = client_ip is not None and self.magic_link_repository.count_created_since(
            since, request_ip=client_ip
        ) >= settings.MAGIC_LINK_RATE_LIMIT_PER_IP
        if over_email or over_ip:
            raise RateLimitExceededError(int(window.total_seconds()))

    def verify_magic_link(self, token: str) -> Optional[Tuple[User, str]]:
        """
        Verify a magic link token and return user with JWT token.
        Creates a new user if the email doesn't exist yet.

        Args:
            token: Magic link token

        Returns:
            Tuple of (User, JWT token) or None if invalid
        """
        # Use the link (and invalidate the email's other links) in one step
        email = self.magic_link_repository.consume(hash_magic_link_token(token))

        if not email:
            return None

        # Get or create user
        user = self.user_repository.get_by_email(email)

        if not user:
            # Create new user with email as username initially.
            # New users always get the default role; only `app.cli grant-role` changes it.
            username = email.split("@")[0]
            if is_reserved_username(username):
                username = "user"
            # Ensure username is unique
            base_username = username
            counter = 1
            while self.user_repository.get_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=email,
                username=username,
                is_active=True
            )
            user = self.user_repository.create(user)

        return user, self.create_session_token(user)

    @staticmethod
    def create_session_token(user: User) -> str:
        """
        Create a session JWT for a user. It stays valid until it expires or
        the user's token_version changes.

        Args:
            user: User to authenticate

        Returns:
            Encoded JWT
        """
        return create_access_token({
            "sub": str(user.id),
            "ver": user.token_version,
            "email": user.email,
            "username": user.username
        })

    def revoke_sessions(self, user: User) -> User:
        """
        Invalidate every session token issued to a user ("log out everywhere").

        Args:
            user: User whose sessions to revoke

        Returns:
            Updated User instance
        """
        user.token_version += 1
        return self.user_repository.update(user)

    def get_current_user(self, user_id: int) -> Optional[User]:
        """
        Get current user by ID.

        Args:
            user_id: User ID from JWT token

        Returns:
            User instance or None if not found
        """
        return self.user_repository.get_by_id(user_id)

    def update_user_profile(
        self,
        user_id: int,
        username: Optional[str] = None
    ) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User ID
            username: New username (optional)

        Returns:
            Updated User instance or None if not found

        Raises:
            UsernameUnavailableError: If the username is reserved or taken
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None

        if username and username != user.username:
            if is_reserved_username(username):
                raise UsernameUnavailableError("Username is reserved")
            existing = self.user_repository.get_by_username(username)
            if existing and existing.id != user_id:
                raise UsernameUnavailableError("Username already taken")
            user.username = username

        return self.user_repository.update(user)
