from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.database import get_db
from app.models import User
from app.schemas.common import StandardResponse
from app.schemas.user import (
    ChangePasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserSafeResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=StandardResponse[UserSafeResponse], status_code=status.HTTP_201_CREATED)
def register_customer(data: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new customer account and creates their customer profile."""
    user_safe = AuthService.register_customer(db, data)
    return StandardResponse(
        success=True,
        message="Registration successful. Welcome to Cloud Kitchen!",
        data=user_safe,
    )


@router.post("/login", response_model=StandardResponse[TokenResponse])
def login(data: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials and returns a signed JWT access token."""
    token_resp = AuthService.login(db, data)
    return StandardResponse(
        success=True,
        message="Login successful",
        data=token_resp,
    )


@router.get("/me", response_model=StandardResponse[UserSafeResponse])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated account profile (never returns password hashes)."""
    return StandardResponse(
        success=True,
        message="Profile retrieved",
        data=UserSafeResponse.model_validate(current_user),
    )


@router.post("/logout", response_model=StandardResponse[dict])
def logout(
    authorization: str = Header(...),
    current_user: User = Depends(get_current_user),
):
    """Revokes the current JWT bearer token via Redis blocklist."""
    token = authorization.replace("Bearer ", "").strip()
    AuthService.logout(token, current_user.user_id)
    return StandardResponse(
        success=True,
        message="Successfully logged out and session revoked",
        data={"revoked": True},
    )


@router.post("/change-password", response_model=StandardResponse[dict])
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verifies existing password and updates to a new strong password."""
    AuthService.change_password(db, current_user, data)
    return StandardResponse(
        success=True,
        message="Password updated successfully. Please log in with your new credentials.",
        data={"updated": True},
    )
