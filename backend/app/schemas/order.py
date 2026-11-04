from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from app.schemas.address import AddressResponse


class OrderCreateRequest(BaseModel):
    delivery_address_id: int
    payment_method: str = Field("UPI", pattern="^(UPI|CREDIT_CARD|DEBIT_CARD|NET_BANKING|WALLET|CASH_ON_DELIVERY)$")
    special_instructions: Optional[str] = Field(None, max_length=500)
    idempotency_key: str = Field(..., min_length=10, max_length=100)


class OrderItemResponse(BaseModel):
    order_item_id: int
    menu_item_id: int
    item_name_snapshot: str
    unit_price_snapshot: Decimal
    quantity: int
    subtotal_price: Decimal
    customization_notes: Optional[str] = None

    class Config:
        from_attributes = True


class OrderStatusHistoryResponse(BaseModel):
    history_id: int
    previous_status: Optional[str] = None
    new_status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    order_id: int
    order_number: str
    kitchen_id: int
    order_status: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    items_count: int = 0
    placed_at: datetime

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    special_instructions: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    delivery_address: Optional[AddressResponse] = None
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=255)
