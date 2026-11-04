from datetime import timedelta
from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.redis import redis_client
from app.models import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import ChangePasswordRequest, TokenResponse, UserLoginRequest, UserRegisterRequest, UserSafeResponse


class AuthService:
    @staticmethod
    def register_customer(db: Session, data: UserRegisterRequest) -> UserSafeResponse:
        # Check duplicate email
        if UserRepository.get_by_email(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists",
            )

        # Check duplicate phone
        if UserRepository.get_by_phone(db, data.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this phone number already exists",
            )

        # Split full name
        parts = data.full_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        # Hash password securely
        hashed = hash_password(data.password)

        user = UserRepository.create_customer(
            db=db,
            email=data.email,
            phone_number=data.phone_number,
            password_hash=hashed,
            first_name=first_name,
            last_name=last_name,
        )

        return UserSafeResponse.model_validate(user)

    @staticmethod
    def login(db: Session, data: UserLoginRequest) -> TokenResponse:
        user = UserRepository.get_by_email(db, data.email)
        # Avoid timing attacks and leaking specific user existence
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive or suspended. Please contact support.",
            )

        # Generate JWT
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        access_token = create_access_token(
            subject=user.user_id,
            expires_delta=timedelta(minutes=expires_minutes),
        )

        # Optional: store active session in Redis
        redis_client.set_json(
            f"session:{user.user_id}",
            {"user_id": user.user_id, "role": user.role.value},
            ttl_seconds=expires_minutes * 60,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_minutes * 60,
            user=UserSafeResponse.model_validate(user),
        )

    @staticmethod
    def logout(token: str, user_id: int) -> bool:
        """Revokes the current token in Redis blocklist matching token expiry."""
        expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        redis_client.set(f"blocklist:{token}", "revoked", ttl_seconds=expires_seconds)
        redis_client.delete(f"session:{user_id}")
        return True

    @staticmethod
    def change_password(db: Session, user: User, data: ChangePasswordRequest) -> bool:
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        new_hash = hash_password(data.new_password)
        UserRepository.update_password(db, user, new_hash)
        # Invalidate active Redis session
        redis_client.delete(f"session:{user.user_id}")
        return True
