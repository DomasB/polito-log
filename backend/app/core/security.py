import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from app.config import settings


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_magic_link_token() -> str:
    """
    Generate a secure random token for magic links.

    Returns:
        Cryptographically secure random token string
    """
    # Generate 32 bytes (256 bits) of random data
    # This is URL-safe and cryptographically secure
    return secrets.token_urlsafe(32)


def verify_magic_link_token(token: str) -> bool:
    """
    Verify that a magic link token is in the correct format.

    Args:
        token: Token string to verify

    Returns:
        True if token format is valid
    """
    # Basic validation - check if token is the right length and format
    # Actual verification happens by checking database
    return len(token) > 20 and token.replace("-", "").replace("_", "").isalnum()
