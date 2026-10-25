from typing import Callable, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.core.security import decode_access_token
from app.core.email import EmailSender, get_email_sender as get_email_sender_factory

# Security scheme for OpenAPI documentation
# auto_error=False: get_current_user answers a missing header with 401 itself
# (HTTPBearer would answer 403).
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="JWT Bearer token authentication",
    auto_error=False
)


async def get_email_sender() -> EmailSender:
    """
    Dependency for getting email sender instance.
    Returns ConsoleEmailSender for development, BrevoEmailSender for production.
    Automatically selects based on ENVIRONMENT and BREVO_API_KEY settings.
    """
    return get_email_sender_factory()


def _user_from_token(token: str, db: Session) -> Optional[User]:
    """
    Resolve a session JWT to its active user.

    The token must carry the user's current token_version in its `ver` claim:
    bumping users.token_version (role change, "log out everywhere") revokes
    every token issued before.

    Args:
        token: Encoded JWT
        db: Database session

    Returns:
        User instance, or None if the token is invalid, expired or revoked
    """
    payload = decode_access_token(token)
    if not payload:
        return None

    try:
        user_id = int(payload["sub"])
        token_version = int(payload["ver"])
    except (KeyError, TypeError, ValueError):
        return None

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active or user.token_version != token_version:
        return None

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT Bearer token (optional).
    Returns None if no token or invalid token.

    Args:
        credentials: Bearer token credentials from Authorization header
        db: Database session

    Returns:
        User instance or None
    """
    if credentials is None:
        return None

    return _user_from_token(credentials.credentials, db)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT Bearer token (required).
    Raises 401 if not authenticated.
    This dependency is integrated with OpenAPI security for Swagger UI.

    Args:
        credentials: Bearer token credentials from Authorization header
        db: Database session

    Returns:
        User instance

    Raises:
        HTTPException: If not authenticated, or the token is invalid, expired
            or revoked, or the user is inactive
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = _user_from_token(credentials.credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(min_role: UserRole) -> Callable[..., User]:
    """
    Build a dependency that admits users whose role is at least `min_role`.
    The role comes from the database (via get_current_user), never from the JWT.

    Usage:
        @router.delete("/{id}", dependencies=[Depends(require_role(UserRole.MODERATOR))])

    Args:
        min_role: Least privileged role that is allowed

    Returns:
        Dependency returning the current user; it raises 401 when not
        authenticated and 403 when the role is insufficient
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role.at_least(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return current_user

    return dependency
