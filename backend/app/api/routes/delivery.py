import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import DeliveryContext, get_current_delivery_person
from app.db.database import get_db
from app.models.fulfillment import DeliveryStatus
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.schemas.delivery import (
    DeliveryAssignmentDetail,
    DeliveryAssignmentItem,
    DeliveryDashboardStats,
    DeliveryPersonAvailabilityUpdate,
    DeliveryPersonProfileOut,
    DeliveryStatusUpdate,
)
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/delivery", tags=["Delivery Management"])


@router.get("/profile", response_model=StandardResponse[DeliveryPersonProfileOut])
def get_delivery_profile(
    driver_ctx: DeliveryContext = Depends(get_current_delivery_person),
    db: Session = Depends(get_db),
):
    """
    Returns profile information for the authenticated delivery courier.
    Delivery personnel can only view their own profile.
    """
    profile = DeliveryService.get_profile(db, driver_ctx)
    return StandardResponse(success=True, data=profile)


@router.patch("/availability", response_model=StandardResponse[DeliveryPersonProfileOut])
def update_delivery_availability(
    data: DeliveryPersonAvailabilityUpdate,
    driver_ctx: DeliveryContext = Depends(get_current_delivery_person),
    db: Session = Depends(get_db),
):
    """
    Toggles delivery availability (AVAILABLE / OFF_DUTY).
    Drivers cannot set themselves AVAILABLE while engaged in an ongoing delivery.
    """
    updated_profile = DeliveryService.update_availability(db, driver_ctx, data.current_status)
    return StandardResponse(
        success=True,
        message=f"Status updated to {data.current_status.value}",
        data=updated_profile,
    )


@router.get("/dashboard", response_model=StandardResponse[DeliveryDashboardStats])
def get_delivery_dashboard(
    driver_ctx: DeliveryContext = Depends(get_current_delivery_person),
    db: Session = Depends(get_db),
):
    """
    Returns real-time dashboard metrics for the authenticated courier:
    assigned deliveries, pending pickup, picked up, out for delivery, and completed today.
    """
    stats = DeliveryService.get_dashboard_stats(db, driver_ctx)
    return StandardResponse(success=True, data=stats)


@router.get("/assignments", response_model=StandardResponse[PaginatedResponse[DeliveryAssignmentItem]])
def list_delivery_assignments(
    status_filter: Optional[DeliveryStatus] = Query(None, alias="status"),
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    driver_ctx: DeliveryContext = Depends(get_current_delivery_person),
    db: Session = Depends(get_db),
):
    """
    Lists orders assigned to the authenticated delivery courier.
    Cross-driver assignments are strictly isolated.
    """
    skip = (page - 1) * limit
    items, total = DeliveryService.list_assignments(
        db=db,
        driver_ctx=driver_ctx,
        delivery_status=status_filter,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )

    total_pages = math.ceil(total / limit) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return StandardResponse(
        success=True,
        data=PaginatedResponse(items=items, meta=meta),
    )


@router.get("/assignments/{delivery_id}", response_model=StandardResponse[DeliveryAssignmentDetail])
def get_delivery_assignment_detail(
    delivery_id: int,
    driver_ctx: DeliveryContext = Depends(get_current_delivery_person),
    db: Session = Depends(get_db),
):
    """
    Retrieves full details of a specific delivery assignment:
    customer address, contact, kitchen address, order items snapshot, and special instructions.
    """
    detail = DeliveryService.get_assignment_detail(db, driver_ctx, delivery_id)
    return StandardResponse(success=True, data=detail)


@router.patch("/assignments/{delivery_id}/status", response_model=StandardResponse[DeliveryAssignmentDetail])
def update_delivery_status(
    delivery_id: int,
    data: DeliveryStatusUpdate,
    driver_ctx: DeliveryContext = Depends(get_current_delivery_person),
    db: Session = Depends(get_db),
):
    """
    Updates the delivery workflow state:
    ASSIGNED -> PICKED_UP -> OUT_FOR_DELIVERY -> DELIVERED.
    Enforces state transitions, kitchen ready check, and prevents duplicate completion.
    """
    updated = DeliveryService.update_delivery_status(db, driver_ctx, delivery_id, data)
    return StandardResponse(
        success=True,
        message=f"Delivery status updated to {data.status.value}",
        data=updated,
    )
