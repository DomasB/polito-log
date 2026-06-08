from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.repositories.user import UserRepository
from app.repositories.magic_link import MagicLinkRepository
from app.models.user import User
from app.models.magic_link import MagicLink
from app.schemas.user import UserCreate
from app.core.security import generate_magic_link_token, create_access_token
from app.core.email import EmailSender
from app.config import settings


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

    async def request_magic_link(self, email: str) -> Tuple[bool, str]:
        """
        Request a magic link for authentication.
        Creates a new user if email doesn't exist.

        Args:
            email: Email address to send magic link to

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if user exists
        user = self.user_repository.get_by_email(email)

        # Generate secure token
        token = generate_magic_link_token()

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )

        # Create magic link record
        magic_link = MagicLink(
            token=token,
            email=email,
            user_id=user.id if user else None,
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

    def verify_magic_link(self, token: str) -> Optional[Tuple[User, str]]:
        """
        Verify a magic link token and return user with JWT token.
        Creates a new user if the email doesn't exist yet.

        Args:
            token: Magic link token

        Returns:
            Tuple of (User, JWT token) or None if invalid
        """
        # Get valid magic link
        magic_link = self.magic_link_repository.get_valid_by_token(token)

        if not magic_link:
            return None

        # Get or create user
        user = self.user_repository.get_by_email(magic_link.email)

        if not user:
            # Create new user with email as username initially
            username = magic_link.email.split("@")[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while self.user_repository.get_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=magic_link.email,
                username=username,
                is_active=True
            )
            user = self.user_repository.create(user)

        # Update last login
        self.user_repository.update(user)

        # Mark magic link as used
        self.magic_link_repository.mark_as_used(magic_link)

        # Create JWT token
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username
        }
        access_token = create_access_token(token_data)

        return user, access_token

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
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None

        if username:
            # Check if username is already taken
            existing = self.user_repository.get_by_username(username)
            if existing and existing.id != user_id:
                return None
            user.username = username

        return self.user_repository.update(user)
