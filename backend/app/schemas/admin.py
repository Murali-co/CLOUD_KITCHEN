from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


from app.models.fulfillment import DeliveryStatus, DiscountType
from app.models.kitchen import OperatingStatus
from app.models.order import OrderStatus, PaymentMethod, PaymentStatus
from app.models.user import DietaryPreference, ShiftTiming, StaffRole, UserRole, VehicleType


# ---------------------------------------------------------
# Admin Dashboard & Metric Schemas
# ---------------------------------------------------------
class AdminDashboardStats(BaseModel):
    total_users: int
    total_customers: int
    total_kitchens: int
    active_kitchens: int
    total_menu_items: int
    total_orders: int
    today_orders: int
    pending_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    today_revenue: Decimal
    low_stock_alerts_count: int


# ---------------------------------------------------------
# User Management Schemas
# ---------------------------------------------------------
class AdminUserOut(BaseModel):
    user_id: int
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Associated role details if applicable
    kitchen_name: Optional[str] = None
    vehicle_number: Optional[str] = None


class AdminUserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Target active status for the account")
    reason: Optional[str] = Field(None, max_length=255)


class AdminUserRoleUpdate(BaseModel):
    role: UserRole = Field(..., description="Target system role (CUSTOMER, ADMIN, KITCHEN_STAFF, DELIVERY_PERSON)")
    reason: Optional[str] = Field(None, max_length=255)


# ---------------------------------------------------------
# Kitchen Management Schemas
# ---------------------------------------------------------
class AdminKitchenCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    street_address: str = Field(..., min_length=5, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=4, max_length=20)
    phone: str = Field(..., min_length=8, max_length=20)
    email: str = Field(..., pattern=EMAIL_REGEX)
    max_orders_per_hour: int = Field(default=50, ge=5, le=500)


class AdminKitchenUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = Field(None, pattern=EMAIL_REGEX)
    max_orders_per_hour: Optional[int] = Field(None, ge=5, le=500)


class AdminKitchenStatusUpdate(BaseModel):
    is_active: Optional[bool] = Field(None, description="Activate or soft-deactivate kitchen facility")
    operating_status: Optional[OperatingStatus] = Field(None, description="Operating status enum: ACTIVE, INACTIVE, MAINTENANCE")
    reason: Optional[str] = Field(None, max_length=255)


class AdminKitchenOut(BaseModel):
    kitchen_id: int
    name: str
    street_address: str
    city: str
    state: str
    postal_code: str
    phone: str
    email: str
    operating_status: OperatingStatus
    is_active: bool
    max_orders_per_hour: int
    active_staff_count: int
    menu_items_count: int
    created_at: datetime


# ---------------------------------------------------------
# Staff Management Schemas
# ---------------------------------------------------------
class AdminStaffCreate(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX)
    password: str = Field(..., min_length=8, description="Initial secure account password")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    kitchen_id: int
    staff_role: StaffRole
    shift_timing: ShiftTiming = ShiftTiming.MORNING


class AdminStaffReassign(BaseModel):
    kitchen_id: Optional[int] = None
    staff_role: Optional[StaffRole] = None
    shift_timing: Optional[ShiftTiming] = None


class AdminStaffOut(BaseModel):
    staff_id: int
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    kitchen_id: int
    kitchen_name: str
    staff_role: StaffRole
    shift_timing: ShiftTiming
    hired_date: date
    is_active: bool


# ---------------------------------------------------------
# Menu & Category Management Schemas
# ---------------------------------------------------------
class AdminCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=255)


class AdminCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None


class AdminCategoryOut(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime


class AdminMenuItemStatusUpdate(BaseModel):
    is_active: Optional[bool] = Field(None, description="Activate or soft-deactivate menu item across store")
    is_available: Optional[bool] = Field(None, description="Availability toggle for menu item")


class AdminMenuItemOut(BaseModel):
    menu_item_id: int
    kitchen_id: int
    kitchen_name: str
    category_id: int
    category_name: str
    name: str
    description: Optional[str] = None
    base_price: Decimal
    is_vegetarian: bool
    is_available: bool
    is_active: bool
    preparation_time_minutes: int
    calories: Optional[int] = None
    created_at: datetime


# ---------------------------------------------------------
# Order & Payment Administration Schemas
# ---------------------------------------------------------
class AdminOrderListItem(BaseModel):
    order_id: int
    order_number: str
    kitchen_id: int
    kitchen_name: str
    customer_id: int
    customer_name: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    delivery_status: Optional[DeliveryStatus] = None
    delivery_person_name: Optional[str] = None
    total_amount: Decimal
    item_count: int
    created_at: datetime


class AdminOrderItemDetail(BaseModel):
    item_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class AdminOrderDetailOut(BaseModel):
    order_id: int
    order_number: str
    kitchen_id: int
    kitchen_name: str
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: str
    delivery_address: Optional[str] = None
    order_status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    subtotal: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    items: List[AdminOrderItemDetail]
    delivery: Optional[Dict[str, Any]] = None
    status_history: List[Dict[str, Any]]
    created_at: datetime


class AdminOrderCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255, description="Administrative cancellation justification")


class AdminPaymentOut(BaseModel):
    payment_id: int
    order_id: int
    order_number: str
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    payment_reference: str
    transaction_reference: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------
# Coupon Administration Schemas
# ---------------------------------------------------------
class AdminCouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=Decimal("0.00"))
    min_order_value: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    max_discount_amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    valid_from: datetime
    valid_to: datetime
    usage_limit_per_user: int = Field(default=1, ge=1)
    total_usage_limit: int = Field(default=1000, ge=1)
    is_active: bool = True


class AdminCouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    min_order_value: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    max_discount_amount: Optional[Decimal] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    usage_limit_per_user: Optional[int] = Field(None, ge=1)
    total_usage_limit: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class AdminCouponOut(BaseModel):
    coupon_id: int
    code: str
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: Decimal
    min_order_value: Decimal
    max_discount_amount: Optional[Decimal] = None
    valid_from: datetime
    valid_to: datetime
    usage_limit_per_user: int
    total_usage_limit: int
    current_usage_count: int
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------
# Platform Analytics Schemas
# ---------------------------------------------------------
class DailyMetricPoint(BaseModel):
    date: str
    orders_count: int
    revenue: Decimal


class PopularItemPoint(BaseModel):
    menu_item_id: int
    name: str
    kitchen_name: str
    total_ordered_quantity: int
    total_revenue: Decimal


class KitchenPerformancePoint(BaseModel):
    kitchen_id: int
    kitchen_name: str
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    completion_rate_percent: Decimal


class StatusDistributionPoint(BaseModel):
    status: str
    count: int


class AdminAnalyticsOverview(BaseModel):
    date_from: str
    date_to: str
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    daily_metrics: List[DailyMetricPoint] = []
    orders_by_day: List[Dict[str, Any]] = []
    revenue_by_day: List[Dict[str, Any]] = []
    popular_items: List[PopularItemPoint] = []
    kitchen_performance: List[KitchenPerformancePoint] = []
    order_status_distribution: List[StatusDistributionPoint] = []
    payment_status_distribution: List[StatusDistributionPoint] = []
    delivery_speed: Dict[str, Any] = {}
    customer_growth: List[Dict[str, Any]] = []


# ---------------------------------------------------------
# Audit Log Schema
# ---------------------------------------------------------
class AdminAuditLogOut(BaseModel):
    audit_id: int
    actor_user_id: int
    actor_name: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
