from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import StaffContext, get_current_kitchen_staff, require_kitchen_manager
from app.db.database import get_db
from app.models.order import OrderStatus
from app.schemas.common import StandardResponse, PaginatedResponse, PaginationMeta
from app.schemas.inventory import RecipeDetailOut, RecipeUpdatePayload
from app.schemas.kitchen_management import (
    KitchenAvailabilityOut,
    KitchenAvailabilityUpdate,
    KitchenDashboardStats,
    KitchenMenuItemCreate,
    KitchenMenuItemOut,
    KitchenMenuItemUpdate,
    KitchenMenuItemAvailabilityUpdate,
    KitchenOrderDetail,
    KitchenOrderListItem,
    KitchenOrderStatusUpdate,
    KitchenQueueItem,
    StaffProfileOut,
)
from app.services.inventory_service import InventoryService
from app.services.kitchen_service import KitchenService

router = APIRouter(prefix="/kitchen", tags=["Kitchen Management"])


# ---------------------------------------------------------
# Staff Profile & Access Info
# ---------------------------------------------------------
@router.get("/me", response_model=StandardResponse[StaffProfileOut])
def get_kitchen_profile(
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns the authenticated kitchen staff member's profile and assigned kitchen."""
    profile = KitchenService.get_staff_profile(staff_ctx, db)
    return StandardResponse(success=True, message="Staff profile retrieved", data=profile)


# ---------------------------------------------------------
# Kitchen Dashboard & Statistics
# ---------------------------------------------------------
@router.get("/dashboard", response_model=StandardResponse[KitchenDashboardStats])
def get_kitchen_dashboard(
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns aggregated real-time operational metrics for the assigned kitchen."""
    stats = KitchenService.get_dashboard_stats(db, staff_ctx)
    return StandardResponse(success=True, message="Kitchen dashboard stats retrieved", data=stats)


# ---------------------------------------------------------
# Order Queue & Order Processing
# ---------------------------------------------------------
@router.get("/queue", response_model=StandardResponse[List[KitchenQueueItem]])
def get_order_queue(
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns the live in-flight kitchen preparation queue with order age and urgency flags."""
    queue = KitchenService.get_order_queue(db, staff_ctx)
    return StandardResponse(success=True, message="Active order queue retrieved", data=queue)


@router.get("/orders", response_model=StandardResponse[PaginatedResponse[KitchenOrderListItem]])
def list_kitchen_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search by order ID or number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Lists orders belonging exclusively to the authenticated staff member's assigned kitchen."""
    date_obj = None
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            pass

    skip = (page - 1) * page_size
    items, total = KitchenService.get_orders(
        db=db,
        staff_ctx=staff_ctx,
        status_filter=status,
        date_filter=date_obj,
        search=search,
        skip=skip,
        limit=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return StandardResponse(
        success=True,
        message="Kitchen orders retrieved",
        data=PaginatedResponse(
            items=items,
            meta=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
    )


@router.get("/orders/{order_id}", response_model=StandardResponse[KitchenOrderDetail])
def get_kitchen_order_detail(
    order_id: int,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Retrieves full order information, ordered items, custom notes, and status timeline."""
    order = KitchenService.get_order_detail(db, staff_ctx, order_id)
    return StandardResponse(success=True, message="Order details retrieved", data=order)


@router.patch("/orders/{order_id}/status", response_model=StandardResponse[KitchenOrderDetail])
def update_kitchen_order_status(
    order_id: int,
    data: KitchenOrderStatusUpdate,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """
    Advances order status along the authorized state machine.
    Transitioning to PREPARING executes atomic recipe-based inventory stock deduction.
    """
    updated = KitchenService.update_order_status(db, staff_ctx, order_id, data)
    return StandardResponse(
        success=True,
        message=f"Order #{order_id} successfully transitioned to {data.status.value}",
        data=updated,
    )


# ---------------------------------------------------------
# Kitchen Menu Management
# ---------------------------------------------------------
@router.get("/menu", response_model=StandardResponse[List[KitchenMenuItemOut]])
def list_kitchen_menu(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Lists menu offerings configured for this kitchen facility."""
    menu_items = KitchenService.get_menu(
        db, staff_ctx, category_id=category_id, search=search, is_available=is_available
    )
    return StandardResponse(success=True, message="Kitchen menu items retrieved", data=menu_items)


@router.post("/menu", response_model=StandardResponse[KitchenMenuItemOut], status_code=status.HTTP_201_CREATED)
def create_kitchen_menu_item(
    data: KitchenMenuItemCreate,
    staff_ctx: StaffContext = Depends(require_kitchen_manager),
    db: Session = Depends(get_db),
):
    """Creates a new menu item for the assigned kitchen (Kitchen Manager only)."""
    item = KitchenService.create_menu_item(db, staff_ctx, data)
    return StandardResponse(success=True, message="Menu item created successfully", data=item)


@router.put("/menu/{item_id}", response_model=StandardResponse[KitchenMenuItemOut])
def update_kitchen_menu_item(
    item_id: int,
    data: KitchenMenuItemUpdate,
    staff_ctx: StaffContext = Depends(require_kitchen_manager),
    db: Session = Depends(get_db),
):
    """Updates menu item details for the assigned kitchen (Kitchen Manager only)."""
    item = KitchenService.update_menu_item(db, staff_ctx, item_id, data)
    return StandardResponse(success=True, message="Menu item updated successfully", data=item)


@router.patch("/menu/{item_id}/availability", response_model=StandardResponse[KitchenMenuItemOut])
def update_menu_item_availability(
    item_id: int,
    data: KitchenMenuItemAvailabilityUpdate,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Quickly toggles item availability (86ing dishes). Available to all kitchen staff."""
    item = KitchenService.update_menu_item_availability(db, staff_ctx, item_id, data.is_available)
    status_str = "available" if data.is_available else "unavailable"
    return StandardResponse(
        success=True, message=f"Item marked as {status_str}", data=item
    )


# ---------------------------------------------------------
# Recipe Management (Bill of Materials)
# ---------------------------------------------------------
@router.get("/menu/{item_id}/recipe", response_model=StandardResponse[RecipeDetailOut])
def get_menu_item_recipe(
    item_id: int,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns the recipe ingredients and quantities required per serving for a menu item."""
    recipe = InventoryService.get_recipe(db, staff_ctx.kitchen_id, item_id)
    return StandardResponse(success=True, message="Recipe retrieved successfully", data=recipe)


@router.put("/menu/{item_id}/recipe", response_model=StandardResponse[RecipeDetailOut])
def update_menu_item_recipe(
    item_id: int,
    payload: RecipeUpdatePayload,
    staff_ctx: StaffContext = Depends(require_kitchen_manager),
    db: Session = Depends(get_db),
):
    """Configures the recipe Bill of Materials for a dish (Kitchen Manager only)."""
    updated_recipe = InventoryService.update_recipe(db, staff_ctx.kitchen_id, item_id, payload)
    return StandardResponse(
        success=True, message="Recipe updated successfully", data=updated_recipe
    )


# ---------------------------------------------------------
# Kitchen Availability / Operating Status
# ---------------------------------------------------------
@router.get("/availability", response_model=StandardResponse[KitchenAvailabilityOut])
def get_kitchen_availability(
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns the kitchen's current operating status (ACTIVE, INACTIVE, MAINTENANCE)."""
    avail = KitchenService.get_availability(db, staff_ctx)
    return StandardResponse(success=True, message="Kitchen availability retrieved", data=avail)


@router.patch("/availability", response_model=StandardResponse[KitchenAvailabilityOut])
def update_kitchen_availability(
    data: KitchenAvailabilityUpdate,
    staff_ctx: StaffContext = Depends(require_kitchen_manager),
    db: Session = Depends(get_db),
):
    """Allows Kitchen Managers to open, pause, or close the kitchen for new orders."""
    updated = KitchenService.update_availability(db, staff_ctx, data)
    return StandardResponse(
        success=True,
        message=f"Kitchen operating status updated to {data.operating_status.value}",
        data=updated,
    )
