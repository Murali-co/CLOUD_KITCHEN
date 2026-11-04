from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.address import AddressResponse


class CheckoutValidateRequest(BaseModel):
    delivery_address_id: int
    coupon_code: Optional[str] = None


class CheckoutSummaryResponse(BaseModel):
    subtotal_amount: Decimal
    discount_amount: Decimal
    delivery_fee: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    kitchen_id: int
    kitchen_name: str
    delivery_address: Optional[AddressResponse] = None
    applied_coupon_code: Optional[str] = None
    items_count: int
    can_place_order: bool = True
    validation_errors: List[str] = []
