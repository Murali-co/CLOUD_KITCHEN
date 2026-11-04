from typing import Optional
from pydantic import BaseModel


class CategoryResponse(BaseModel):
    category_id: int
    name: str
    slug: str
    description: Optional[str] = None
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True
