from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CuisineResponse(BaseModel):
    cuisine_id: int
    cuisine_name: str
    cuisine_slug: str
    cuisine_description: Optional[str] = None
    cuisine_image_url: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CuisineDetailResponse(CuisineResponse):
    item_count: int = 0
