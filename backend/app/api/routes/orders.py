from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_customer
from app.db.database import get_db
from app.models import User
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.delivery import OrderTrackingOut
from app.schemas.order import (
    OrderCancelRequest,
    OrderCreateRequest,
    OrderDetailResponse,
    OrderResponse,
)
from app.services.delivery_service import DeliveryService
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=StandardResponse[OrderDetailResponse], status_code=status.HTTP_201_CREATED)
def place_order(
    data: OrderCreateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Creates a new order atomically with idempotency protection and item price snapshots."""
    order_detail = OrderService.place_order(db, current_user.user_id, data)
    return StandardResponse(
        success=True,
        message=f"Order '{order_detail.order_number}' placed successfully!",
        data=order_detail,
    )


@router.get("", response_model=StandardResponse[PaginatedResponse[OrderResponse]])
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Retrieves paginated order history for the authenticated customer."""
    paginated = OrderService.list_customer_orders(db, current_user.user_id, page=page, page_size=page_size)
    return StandardResponse(success=True, data=paginated)


@router.get("/{order_id}", response_model=StandardResponse[OrderDetailResponse])
def get_order_detail(
    order_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Retrieves detailed order progress, item snapshots, and tracking history."""
    detail = OrderService.get_order_detail(db, order_id, current_user.user_id)
    return StandardResponse(success=True, data=detail)


@router.post("/{order_id}/cancel", response_model=StandardResponse[OrderDetailResponse])
def cancel_order(
    order_id: int,
    data: OrderCancelRequest = None,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Cancels order if it has not yet advanced to kitchen preparation."""
    reason = data.reason if data else None
    cancelled = OrderService.cancel_order(db, order_id, current_user.user_id, reason=reason)
    return StandardResponse(
        success=True,
        message="Order cancelled successfully",
        data=cancelled,
    )


@router.get("/{order_id}/tracking", response_model=StandardResponse[OrderTrackingOut])
def get_order_tracking(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Status-based delivery tracking.
    Accessible by:
    - Customer who placed the order
    - Assigned courier
    - Administrators
    Cross-customer tracking is strictly forbidden.
    """
    tracking = DeliveryService.get_order_tracking(db, order_id, current_user)
    return StandardResponse(success=True, data=tracking)

