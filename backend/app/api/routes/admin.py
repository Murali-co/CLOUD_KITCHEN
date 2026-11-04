import math
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.db.database import get_db
from app.models.kitchen import OperatingStatus
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.models.user import StaffRole, User, UserRole
from app.schemas.admin import (
    AdminAnalyticsOverview,
    AdminAuditLogOut,
    AdminCategoryCreate,
    AdminCategoryOut,
    AdminCategoryUpdate,
    AdminCouponCreate,
    AdminCouponOut,
    AdminCouponUpdate,
    AdminDashboardStats,
    AdminKitchenCreate,
    AdminKitchenOut,
    AdminKitchenStatusUpdate,
    AdminKitchenUpdate,
    AdminMenuItemOut,
    AdminMenuItemStatusUpdate,
    AdminOrderDetailOut,
    AdminOrderListItem,
    AdminPaymentOut,
    AdminStaffCreate,
    AdminStaffOut,
    AdminStaffReassign,
    AdminUserOut,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.schemas.delivery import (
    AvailablePersonnelOut,
    DeliveryAssignRequest,
    DeliveryAssignmentDetail,
)
from app.services.admin_service import AdminService
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/admin", tags=["Administrator Dashboard"], dependencies=[Depends(require_admin)])


# -------------------------------------------------------------------------
# 1. Dashboard Overview Metrics
# -------------------------------------------------------------------------
@router.get("/dashboard", response_model=StandardResponse[AdminDashboardStats])
def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Returns platform-wide metrics: user count, kitchens, orders,
    cancelled orders, verified net revenue, and low-stock alerts.
    """
    stats = AdminService.get_dashboard_metrics(db)
    return StandardResponse(success=True, data=stats)


# -------------------------------------------------------------------------
# 2. User Management
# -------------------------------------------------------------------------
@router.get("/users", response_model=StandardResponse[PaginatedResponse[AdminUserOut]])
def list_users(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive accounts"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists users with search, role filters, and pagination."""
    skip = (page - 1) * page_size
    users, total = AdminService.list_users(
        db, search=search, role=role, is_active=is_active, skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=users, meta=meta))


@router.get("/users/{user_id}", response_model=StandardResponse[AdminUserOut])
def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    """Retrieves full user details without exposing password hashes."""
    user = AdminService.get_user(db, user_id)
    return StandardResponse(success=True, data=user)


@router.patch("/users/{user_id}/status", response_model=StandardResponse[AdminUserOut])
def update_user_status(
    user_id: int,
    data: AdminUserStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Activates or deactivates a user account.
    Blocks deactivation of the last remaining active administrator.
    """
    updated = AdminService.update_user_status(db, user_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"User status updated to {'Active' if data.is_active else 'Deactivated'}",
        data=updated,
    )


@router.patch("/users/{user_id}/role", response_model=StandardResponse[AdminUserOut])
def update_user_role(
    user_id: int,
    data: AdminUserRoleUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Changes a user's role.
    Blocks demoting the last active administrator.
    """
    updated = AdminService.update_user_role(db, user_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"User role updated to {data.role.value}",
        data=updated,
    )


# -------------------------------------------------------------------------
# 3. Kitchen Management
# -------------------------------------------------------------------------
@router.get("/kitchens", response_model=StandardResponse[PaginatedResponse[AdminKitchenOut]])
def list_kitchens(
    search: Optional[str] = Query(None, description="Search kitchen name, code, or city"),
    status_filter: Optional[OperatingStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists cloud kitchen facilities across the platform."""
    skip = (page - 1) * page_size
    kitchens, total = AdminService.list_kitchens(
        db, search=search, status_filter=status_filter, skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=kitchens, meta=meta))


@router.post("/kitchens", response_model=StandardResponse[AdminKitchenOut], status_code=status.HTTP_201_CREATED)
def create_kitchen(
    data: AdminKitchenCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Creates a new cloud kitchen facility and logs an audit record."""
    kitchen = AdminService.create_kitchen(db, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Kitchen '{kitchen.name}' created successfully",
        data=kitchen,
    )


@router.get("/kitchens/{kitchen_id}", response_model=StandardResponse[AdminKitchenOut])
def get_kitchen_detail(kitchen_id: int, db: Session = Depends(get_db)):
    """Retrieves kitchen operational details, staff count, and menu count."""
    kitchen = AdminService.get_kitchen(db, kitchen_id)
    return StandardResponse(success=True, data=kitchen)


@router.put("/kitchens/{kitchen_id}", response_model=StandardResponse[AdminKitchenOut])
def update_kitchen(
    kitchen_id: int,
    data: AdminKitchenUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Updates kitchen facility contact and operational details."""
    updated = AdminService.update_kitchen(db, kitchen_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message="Kitchen updated successfully",
        data=updated,
    )


@router.patch("/kitchens/{kitchen_id}/status", response_model=StandardResponse[AdminKitchenOut])
def update_kitchen_status(
    kitchen_id: int,
    data: AdminKitchenStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggles kitchen operating status (OPEN, CLOSED, PAUSED, MAINTENANCE)."""
    updated = AdminService.update_kitchen_status(db, kitchen_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Kitchen operating status updated to {updated.operating_status.value}",
        data=updated,
    )


# -------------------------------------------------------------------------
# 4. Staff Management
# -------------------------------------------------------------------------
@router.get("/staff", response_model=StandardResponse[PaginatedResponse[AdminStaffOut]])
def list_staff(
    kitchen_id: Optional[int] = Query(None, description="Filter by kitchen assignment"),
    role: Optional[StaffRole] = Query(None, description="Filter by staff role"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists staff members across all kitchen locations."""
    skip = (page - 1) * page_size
    staff_members, total = AdminService.list_staff(
        db, kitchen_id=kitchen_id, role=role, skip=skip, limit=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=staff_members, meta=meta))


@router.post("/staff", response_model=StandardResponse[AdminStaffOut], status_code=status.HTTP_201_CREATED)
def create_staff(
    data: AdminStaffCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Creates a new staff account securely with hashed password,
    linking the user to the designated kitchen and staff role.
    """
    staff_out = AdminService.create_staff(db, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Staff account for '{staff_out.full_name}' created successfully",
        data=staff_out,
    )


@router.patch("/staff/{staff_id}/reassign", response_model=StandardResponse[AdminStaffOut])
def reassign_staff(
    staff_id: int,
    data: AdminStaffReassign,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reassigns staff member to a new kitchen, shift timing, or role."""
    updated = AdminService.reassign_staff(db, staff_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message="Staff assignment updated successfully",
        data=updated,
    )


# -------------------------------------------------------------------------
# 5. Menu & Category Administration
# -------------------------------------------------------------------------
@router.get("/menu", response_model=StandardResponse[PaginatedResponse[AdminMenuItemOut]])
def list_menu_items(
    kitchen_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists menu items across all kitchens."""
    skip = (page - 1) * page_size
    items, total = AdminService.list_menu_items(
        db,
        kitchen_id=kitchen_id,
        category_id=category_id,
        search=search,
        is_available=is_available,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=items, meta=meta))


@router.patch("/menu/{item_id}/status", response_model=StandardResponse[AdminMenuItemOut])
def update_menu_item_status(
    item_id: int,
    data: AdminMenuItemStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggles menu item availability across the platform."""
    updated = AdminService.update_menu_item_status(db, item_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Menu item status updated to {'Available' if updated.is_available else 'Unavailable'}",
        data=updated,
    )


@router.get("/categories", response_model=StandardResponse[List[AdminCategoryOut]])
def list_categories(db: Session = Depends(get_db)):
    """Lists all food categories."""
    categories = AdminService.list_categories(db)
    return StandardResponse(success=True, data=categories)


@router.post("/categories", response_model=StandardResponse[AdminCategoryOut], status_code=status.HTTP_201_CREATED)
def create_category(
    data: AdminCategoryCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Creates a new food category."""
    cat = AdminService.create_category(db, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Category '{cat.name}' created successfully",
        data=cat,
    )


@router.put("/categories/{category_id}", response_model=StandardResponse[AdminCategoryOut])
def update_category(
    category_id: int,
    data: AdminCategoryUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Updates food category name, description, image, or status."""
    cat = AdminService.update_category(db, category_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message="Category updated successfully",
        data=cat,
    )


# -------------------------------------------------------------------------
# 6. Order Administration
# -------------------------------------------------------------------------
@router.get("/orders", response_model=StandardResponse[PaginatedResponse[AdminOrderListItem]])
def list_orders(
    search: Optional[str] = Query(None, description="Search by order number or customer phone"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    kitchen_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists all orders across all kitchens with comprehensive filters."""
    skip = (page - 1) * page_size
    orders, total = AdminService.list_orders(
        db,
        search=search,
        status_filter=status_filter,
        kitchen_id=kitchen_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=orders, meta=meta))


@router.get("/orders/{order_id}", response_model=StandardResponse[AdminOrderDetailOut])
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    """Retrieves full order inspection details including items snapshot, timeline, payment, and courier."""
    order = AdminService.get_order(db, order_id)
    return StandardResponse(success=True, data=order)


@router.post("/orders/{order_id}/cancel", response_model=StandardResponse[AdminOrderDetailOut])
def cancel_order_admin(
    order_id: int,
    reason: Optional[str] = Query("Administrative cancellation"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Administratively cancels an eligible order and records audit log."""
    cancelled = AdminService.cancel_order_admin(db, order_id, reason, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Order #{cancelled.order_number} cancelled by administrator",
        data=cancelled,
    )


# -------------------------------------------------------------------------
# 7. Delivery Assignment (Administrator-Authorized)
# -------------------------------------------------------------------------
@router.get("/delivery/available-personnel", response_model=StandardResponse[List[AvailablePersonnelOut]])
def get_available_delivery_personnel(db: Session = Depends(get_db)):
    """Returns couriers currently marked AVAILABLE and not busy on active tasks."""
    personnel = DeliveryService.get_available_personnel(db)
    return StandardResponse(success=True, data=personnel)


@router.post("/orders/{order_id}/assign-delivery", response_model=StandardResponse[DeliveryAssignmentDetail])
def assign_delivery_person(
    order_id: int,
    data: DeliveryAssignRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Assigns an eligible, available delivery courier to an order.
    Verifies order and courier availability, prevents duplicates and conflicts,
    and records an audit log.
    """
    assignment = DeliveryService.assign_delivery_to_order(
        db, order_id=order_id, delivery_person_id=data.delivery_person_id, admin_user_id=admin.user_id
    )
    return StandardResponse(
        success=True,
        message=f"Courier assigned successfully to Order #{assignment.order_number}",
        data=assignment,
    )


# -------------------------------------------------------------------------
# 8. Payment Monitoring
# -------------------------------------------------------------------------
@router.get("/payments", response_model=StandardResponse[PaginatedResponse[AdminPaymentOut]])
def list_payments(
    search: Optional[str] = Query(None, description="Search by transaction reference or gateway payment ID"),
    status_filter: Optional[PaymentStatus] = Query(None, alias="status"),
    method: Optional[PaymentMethod] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists payments across the platform without exposing sensitive payment credentials."""
    skip = (page - 1) * page_size
    payments, total = AdminService.list_payments(
        db,
        search=search,
        status_filter=status_filter,
        method=method,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=payments, meta=meta))


# -------------------------------------------------------------------------
# 9. Coupon Administration
# -------------------------------------------------------------------------
@router.get("/coupons", response_model=StandardResponse[PaginatedResponse[AdminCouponOut]])
def list_coupons(
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists coupons with pagination."""
    skip = (page - 1) * page_size
    coupons, total = AdminService.list_coupons(db, active_only=active_only, skip=skip, limit=page_size)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=coupons, meta=meta))


@router.post("/coupons", response_model=StandardResponse[AdminCouponOut], status_code=status.HTTP_201_CREATED)
def create_coupon(
    data: AdminCouponCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Creates a new coupon with server-side validation constraints."""
    coupon = AdminService.create_coupon(db, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Coupon '{coupon.code}' created successfully",
        data=coupon,
    )


@router.put("/coupons/{coupon_id}", response_model=StandardResponse[AdminCouponOut])
def update_coupon(
    coupon_id: int,
    data: AdminCouponUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Updates coupon parameters and activation state."""
    coupon = AdminService.update_coupon(db, coupon_id, data, admin.user_id)
    return StandardResponse(
        success=True,
        message=f"Coupon '{coupon.code}' updated successfully",
        data=coupon,
    )


# -------------------------------------------------------------------------
# 10. Platform Analytics
# -------------------------------------------------------------------------
@router.get("/analytics/overview", response_model=StandardResponse[AdminAnalyticsOverview])
def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of past days to analyze"),
    db: Session = Depends(get_db),
):
    """
    Returns platform analytics: orders by day, net revenue by day,
    top menu items, kitchen performance, order/payment status breakdown,
    delivery speed metrics, and customer acquisition.
    """
    analytics = AdminService.get_analytics_overview(db, days=days)
    return StandardResponse(success=True, data=analytics)


# -------------------------------------------------------------------------
# 11. Administrative Audit Logs
# -------------------------------------------------------------------------
@router.get("/audit-logs", response_model=StandardResponse[PaginatedResponse[AdminAuditLogOut]])
def list_audit_logs(
    actor_user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists administrative audit logs for compliance and accountability."""
    skip = (page - 1) * page_size
    logs, total = AdminService.list_audit_logs(
        db,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    meta = PaginationMeta(
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return StandardResponse(success=True, data=PaginatedResponse(items=logs, meta=meta))
