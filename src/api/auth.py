"""
CivicPulse — JWT Authentication

Bearer token auth with 8-hour expiry. Roles: coordinator, admin, readonly.
Never logs the token itself — only user_id.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User UUID
        email: User email
        role: User role (coordinator, admin, readonly)
        expires_delta: Custom expiry duration

    Returns:
        Encoded JWT string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiry_hours)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    # Never log the token itself — only the user_id
    logger.info("Token created for user_id=%s role=%s expires=%s", user_id, role, expire.isoformat())

    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Returns:
        Decoded payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.debug("Token decode failed: %s", e)
        return None
