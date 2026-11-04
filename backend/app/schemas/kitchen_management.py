from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
import enum
from pydantic import BaseModel, Field, ConfigDict

from app.models.kitchen import OperatingStatus
from app.models.order import OrderStatus, PaymentStatus, PaymentMethod
from app.models.user import StaffRole


# ---------------------------------------------------------
# Staff Profile & Context
# ---------------------------------------------------------
class StaffProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    staff_id: int
    kitchen_id: int
    staff_role: StaffRole
    kitchen_name: str
    branch_code: str
    shift_timing: str
    hired_date: date


# ---------------------------------------------------------
# Kitchen Availability & Operating Status
# ---------------------------------------------------------
class KitchenAvailabilityOut(BaseModel):
    kitchen_id: int
    name: str
    branch_code: str
    operating_status: OperatingStatus
    opening_time: str
    closing_time: str
    max_active_orders: int
    is_open: bool


class KitchenAvailabilityUpdate(BaseModel):
    operating_status: OperatingStatus
    max_active_orders: Optional[int] = Field(None, ge=1, le=200)


# ---------------------------------------------------------
# Kitchen Dashboard Statistics
# ---------------------------------------------------------
class RecentOrderActivity(BaseModel):
    order_id: int
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    placed_at: datetime
    customer_name: str


class KitchenDashboardStats(BaseModel):
    kitchen_id: int
    kitchen_name: str
    operating_status: OperatingStatus
    total_orders_today: int
    new_orders: int
    confirmed_orders: int
    preparing_orders: int
    ready_orders: int
    completed_orders: int
    cancelled_orders: int
    active_orders_count: int
    max_active_orders: int
    capacity_percentage: float
    low_stock_count: int
    recent_activity: List[RecentOrderActivity]


# ---------------------------------------------------------
# Kitchen Order Management & Queue
# ---------------------------------------------------------
class KitchenOrderItemOut(BaseModel):
    order_item_id: int
    menu_item_id: int
    item_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    customization_notes: Optional[str] = None


class KitchenOrderStatusHistoryOut(BaseModel):
    history_id: int
    previous_status: Optional[OrderStatus] = None
    new_status: OrderStatus
    changed_by_user_id: Optional[int] = None
    changed_by_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class KitchenOrderListItem(BaseModel):
    order_id: int
    order_number: str
    customer_id: int
    customer_name: str
    customer_phone: str
    order_status: OrderStatus
    subtotal_amount: Decimal
    total_amount: Decimal
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    placed_at: datetime
    item_count: int
    special_instructions: Optional[str] = None


class KitchenOrderDetail(BaseModel):
    order_id: int
    order_number: str
    kitchen_id: int
    customer_id: int
    customer_name: str
    customer_phone: str
    delivery_address: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    special_instructions: Optional[str] = None
    placed_at: datetime
    items: List[KitchenOrderItemOut]
    timeline: List[KitchenOrderStatusHistoryOut]


class KitchenOrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = Field(None, max_length=500)


class KitchenQueueItem(BaseModel):
    order_id: int
    order_number: str
    order_status: OrderStatus
    placed_at: datetime
    order_age_minutes: int
    is_urgent: bool
    customer_name: str
    items_summary: List[str]
    item_count: int
    special_instructions: Optional[str] = None


# ---------------------------------------------------------
# Kitchen Menu Management
# ---------------------------------------------------------
class KitchenMenuItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category_id: int
    description: Optional[str] = None
    base_price: Decimal = Field(..., ge=Decimal("0.00"))
    is_vegetarian: bool = False
    is_available: bool = True
    preparation_time_minutes: int = Field(default=15, ge=1, le=180)
    calories: Optional[int] = Field(None, ge=0)


class KitchenMenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    category_id: Optional[int] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    is_vegetarian: Optional[bool] = None
    is_available: Optional[bool] = None
    preparation_time_minutes: Optional[int] = Field(None, ge=1, le=180)
    calories: Optional[int] = Field(None, ge=0)


class KitchenMenuItemAvailabilityUpdate(BaseModel):
    is_available: bool


class KitchenMenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    menu_item_id: int
    kitchen_id: int
    category_id: int
    category_name: Optional[str] = "General"
    name: str
    description: Optional[str] = None
    base_price: Decimal
    is_vegetarian: bool
    is_available: bool
    preparation_time_minutes: int
    calories: Optional[int] = None
    has_recipe: bool = False
    created_at: datetime
    updated_at: datetime
