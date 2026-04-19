"""
CivicPulse — Auth Routes
POST /api/v1/auth/login — authenticate and get JWT
POST /api/v1/auth/refresh — refresh expiring token
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_access_token, verify_password, hash_password
from config import settings
from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, UserCreate
from schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT token."""
    try:
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "status": "error",
                    "code": "ACCOUNT_DISABLED",
                    "message": "Account has been deactivated. Contact administrator.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        token = create_access_token(str(user.id), user.email, user.role)

        return APIResponse(
            data=TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in=settings.jwt_expiry_hours * 3600,
            ).model_dump()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during login.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@router.post("/refresh")
async def refresh_token(user: User = Depends(get_current_user)):
    """Refresh an expiring JWT token."""
    token = create_access_token(str(user.id), user.email, user.role)
    return APIResponse(
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expiry_hours * 3600,
        ).model_dump()
    )


@router.post("/register")
async def register(
    request: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user. First user gets admin role."""
    try:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == request.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "code": "EMAIL_EXISTS",
                    "message": "A user with this email already exists.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Check if this is the first user — auto-promote to admin
        count_result = await db.execute(select(User))
        users = count_result.scalars().all()
        role = "admin" if len(users) == 0 else request.role

        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            role=role,
            city_id=request.city_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        token = create_access_token(str(user.id), user.email, user.role)

        return APIResponse(
            data={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role,
                "access_token": token,
                "token_type": "bearer",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "code": "INTERNAL_ERROR",
                "message": "Registration failed.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
