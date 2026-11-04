from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel


class MenuItemResponse(BaseModel):
    menu_item_id: int
    kitchen_id: int
    category_id: int
    cuisine_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    base_price: Decimal
    is_vegetarian: bool
    is_available: bool
    preparation_time_minutes: int
    calories: Optional[int] = None

    class Config:
        from_attributes = True


class MenuItemDetailResponse(MenuItemResponse):
    kitchen_name: Optional[str] = None
    category_name: Optional[str] = None
    cuisine_name: Optional[str] = None
    ingredients: Optional[List[str]] = []
