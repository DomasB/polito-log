from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import (
    MagicLinkRequest,
    MagicLinkResponse,
    TokenResponse,
    TokenVerify
)
from app.schemas.user import UserResponse, UserUpdate
from app.core.dependencies import get_email_sender, get_current_user
from app.core.email import EmailSender
from app.models.user import User
from app.config import settings


router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)


def get_auth_service(
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender)
) -> AuthService:
    """Dependency for getting AuthService instance."""
    return AuthService(db, email_sender)


@router.post(
    "/magic-link",
    response_model=MagicLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Request magic link for authentication"
)
async def request_magic_link(
    request: MagicLinkRequest,
    service: AuthService = Depends(get_auth_service)
) -> MagicLinkResponse:
    """
    Request a magic link for passwordless authentication.
    Sends an email with a magic link that can be used to log in.
    Creates a new user if the email doesn't exist yet.

    Args:
        request: Magic link request with email
        service: Auth service instance

    Returns:
        Response with success message

    Raises:
        HTTPException: 500 if failed to send email
    """
    success, message = await service.request_magic_link(request.email)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

    return MagicLinkResponse(
        message=message,
        email=request.email
    )


@router.post(
    "/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify magic link and get access token"
)
def verify_magic_link(
    token_verify: TokenVerify,
    service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Verify a magic link token and return a JWT access token.
    Creates a new user if the email doesn't exist yet.

    Args:
        token_verify: Token verification request
        service: Auth service instance

    Returns:
        JWT access token and user information

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    result = service.verify_magic_link(token_verify.token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link"
        )

    user, access_token = result

    # Calculate token expiration
    expires_at = datetime.utcnow() + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role
        }
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get the current authenticated user's profile.

    Args:
        current_user: Current authenticated user from JWT

    Returns:
        User profile information
    """
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile"
)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Update the current authenticated user's profile.

    Args:
        user_update: User update data
        current_user: Current authenticated user from JWT
        service: Auth service instance

    Returns:
        Updated user profile

    Raises:
        HTTPException: 400 if username is already taken
    """
    updated_user = service.update_user_profile(
        user_id=current_user.id,
        username=user_update.username
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    return updated_user
