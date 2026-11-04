from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class CartItemAddRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(1, ge=1, le=50)
    customization_notes: Optional[str] = Field(None, max_length=255)


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=50)
    customization_notes: Optional[str] = Field(None, max_length=255)


class ApplyCouponRequest(BaseModel):
    coupon_code: str = Field(..., min_length=2, max_length=50)


class CartItemResponse(BaseModel):
    menu_item_id: int
    name: str
    unit_price: Decimal
    quantity: int
    subtotal_price: Decimal
    is_available: bool = True
    customization_notes: Optional[str] = None


class CartResponse(BaseModel):
    items: List[CartItemResponse] = []
    subtotal_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    delivery_fee: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    kitchen_id: Optional[int] = None
    kitchen_name: Optional[str] = None
    applied_coupon_code: Optional[str] = None
    items_count: int = 0
