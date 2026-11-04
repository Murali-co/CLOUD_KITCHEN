from datetime import time
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel


class KitchenResponse(BaseModel):
    kitchen_id: int
    name: str
    branch_code: str
    contact_phone: str
    email: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    operating_status: str
    opening_time: time
    closing_time: time
    max_active_orders: int

    class Config:
        from_attributes = True


class KitchenDetailResponse(KitchenResponse):
    menu_items_count: Optional[int] = 0
