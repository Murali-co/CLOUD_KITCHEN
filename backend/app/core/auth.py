from typing import Callable, List, Optional
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.redis import redis_client
from app.models import User, UserRole
from app.models.user import DeliveryPerson, DeliveryPersonStatus, Staff, StaffRole

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates the JWT bearer token, checks Redis revocation blocklist,
    and loads the authenticated, active user from the database.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check Redis revocation blocklist (if available)
    if redis_client.get(f"blocklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled",
        )

    return user


def require_roles(allowed_roles: List[UserRole]) -> Callable[[User], User]:
    """
    Factory dependency to enforce Role-Based Access Control (RBAC).
    Verifies the user's role against the allowed roles list.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource",
            )
        return current_user

    return role_checker


# Specific role dependencies
require_customer = require_roles([UserRole.CUSTOMER])
require_admin = require_roles([UserRole.ADMIN])
require_kitchen_staff = require_roles([UserRole.KITCHEN_STAFF, UserRole.ADMIN])
require_delivery = require_roles([UserRole.DELIVERY_PERSON, UserRole.ADMIN])


@dataclass
class StaffContext:
    user: User
    staff: Optional[Staff]
    kitchen_id: int
    staff_role: StaffRole
    is_manager: bool


def get_current_kitchen_staff(
    current_user: User = Depends(require_kitchen_staff),
    x_kitchen_id: Optional[int] = Header(None, alias="X-Kitchen-Id"),
    db: Session = Depends(get_db),
) -> StaffContext:
    """
    Validates kitchen staff access.
    - If user is KITCHEN_STAFF, strictly loads their assigned kitchen from the staff table.
      Frontend kitchen IDs are NEVER trusted for regular staff.
    - If user is ADMIN, allows switching kitchens via X-Kitchen-Id header (defaults to 1).
    """
    staff = db.query(Staff).filter(Staff.staff_id == current_user.user_id).first()

    if current_user.role == UserRole.ADMIN:
        assigned_kitchen_id = x_kitchen_id or 1
        staff_role = StaffRole.KITCHEN_MANAGER
        is_mgr = True
    else:
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not linked to any kitchen facility",
            )
        assigned_kitchen_id = staff.kitchen_id
        staff_role = staff.staff_role
        is_mgr = staff.staff_role == StaffRole.KITCHEN_MANAGER

    return StaffContext(
        user=current_user,
        staff=staff,
        kitchen_id=assigned_kitchen_id,
        staff_role=staff_role,
        is_manager=is_mgr,
    )


def require_kitchen_manager(
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
) -> StaffContext:
    """
    Enforces Kitchen Manager (or Admin) privileges.
    Line cooks, packers, and general staff are forbidden from executing manager-only actions.
    """
    if not staff_ctx.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kitchen Manager authorization required for this action",
        )
    return staff_ctx


@dataclass
class DeliveryContext:
    user: User
    delivery_person: DeliveryPerson
    delivery_person_id: int
    current_status: DeliveryPersonStatus


def get_current_delivery_person(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeliveryContext:
    """
    Validates delivery personnel access.
    - If user has DELIVERY_PERSON role (or ADMIN), looks up their delivery_person record.
    - Strictly isolates access to their own assignments.
    """
    if current_user.role not in [UserRole.DELIVERY_PERSON, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized delivery personnel",
        )

    driver = db.query(DeliveryPerson).filter(DeliveryPerson.delivery_person_id == current_user.user_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account does not have a linked delivery driver profile",
        )

    return DeliveryContext(
        user=current_user,
        delivery_person=driver,
        delivery_person_id=driver.delivery_person_id,
        current_status=driver.current_status,
    )

