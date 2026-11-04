from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.fulfillment import DeliveryStatus
from app.models.order import OrderStatus
from app.models.user import DeliveryPersonStatus, VehicleType


class DeliveryPersonProfileOut(BaseModel):
    delivery_person_id: int
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    vehicle_type: VehicleType
    vehicle_number: str
    driving_license_number: str
    current_status: DeliveryPersonStatus
    rating: Decimal
    created_at: datetime


class DeliveryPersonAvailabilityUpdate(BaseModel):
    current_status: DeliveryPersonStatus = Field(
        ..., description="Desired driver availability: AVAILABLE or OFF_DUTY"
    )


class DeliveryDashboardStats(BaseModel):
    assigned_deliveries: int
    pending_pickup: int
    picked_up_orders: int
    out_for_delivery_orders: int
    delivered_orders_today: int
    current_status: DeliveryPersonStatus


class DeliveryAssignmentItem(BaseModel):
    delivery_id: int
    order_id: int
    order_number: str
    delivery_status: DeliveryStatus
    order_status: OrderStatus
    kitchen_name: str
    kitchen_address: str
    kitchen_phone: Optional[str] = None
    delivery_address: str
    customer_name: str
    customer_phone: Optional[str] = None
    total_amount: Decimal
    payment_method: str
    payment_status: str
    assigned_at: datetime
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class DeliveryItemSummary(BaseModel):
    item_name: str
    quantity: int


class DeliveryAssignmentDetail(BaseModel):
    delivery_id: int
    order_id: int
    order_number: str
    delivery_status: DeliveryStatus
    order_status: OrderStatus
    kitchen_id: int
    kitchen_name: str
    kitchen_address: str
    kitchen_phone: Optional[str] = None
    delivery_address: str
    customer_name: str
    customer_phone: Optional[str] = None
    items: List[DeliveryItemSummary]
    total_amount: Decimal
    payment_method: str
    payment_status: str
    special_instructions: Optional[str] = None
    delivery_notes: Optional[str] = None
    delivery_otp: Optional[str] = None
    assigned_at: datetime
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus = Field(
        ..., description="Next state in workflow: PICKED_UP, OUT_FOR_DELIVERY, DELIVERED"
    )
    delivery_otp: Optional[str] = Field(None, max_length=6, description="Optional handoff OTP verification")
    notes: Optional[str] = Field(None, max_length=500, description="Transit or delivery notes")
    signature_url: Optional[str] = Field(None, max_length=255)


class DeliveryAssignRequest(BaseModel):
    delivery_person_id: int = Field(..., description="ID of the eligible, available delivery courier")


class AvailablePersonnelOut(BaseModel):
    delivery_person_id: int
    full_name: str
    phone: Optional[str] = None
    vehicle_type: VehicleType
    vehicle_number: str
    rating: Decimal
    current_status: DeliveryPersonStatus


class TrackingStatusPoint(BaseModel):
    status: str
    changed_at: datetime
    notes: Optional[str] = None


class OrderTrackingOut(BaseModel):
    order_id: int
    order_number: str
    order_status: OrderStatus
    delivery_status: Optional[DeliveryStatus] = None
    kitchen_name: str
    kitchen_address: str
    delivery_address: str
    delivery_person_name: Optional[str] = None
    delivery_person_phone: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    vehicle_number: Optional[str] = None
    timeline: List[TrackingStatusPoint]
    created_at: datetime
    estimated_delivery_time: Optional[datetime] = None
