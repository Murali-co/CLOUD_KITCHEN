from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.menu import MenuItemDetailResponse, MenuItemResponse
from app.services.kitchen_service import MenuService

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("", response_model=StandardResponse[PaginatedResponse[MenuItemResponse]])
def search_menu(
    kitchen_id: Optional[int] = Query(None, description="Filter by kitchen branch"),
    category_id: Optional[int] = Query(None, description="Filter by food category"),
    cuisine_id: Optional[int] = Query(None, description="Filter by cuisine style"),
    search: Optional[str] = Query(None, description="Search by dish name"),
    is_vegetarian: Optional[bool] = Query(None, description="Filter vegetarian dishes"),
    is_available: Optional[bool] = Query(True, description="Filter in-stock items"),
    sort_by: Optional[str] = Query(None, description="Sort options: price_asc, price_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Searches menu catalog with kitchen, category, cuisine, dietary, and keyword filters."""
    paginated = MenuService.search_menu(
        db=db,
        kitchen_id=kitchen_id,
        category_id=category_id,
        cuisine_id=cuisine_id,
        search=search,
        is_vegetarian=is_vegetarian,
        is_available=is_available,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return StandardResponse(success=True, data=paginated)


@router.get("/{item_id}", response_model=StandardResponse[MenuItemDetailResponse])
def get_menu_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves single dish details, constituent ingredients, and preparing kitchen."""
    detail = MenuService.get_menu_detail(db, item_id)
    return StandardResponse(success=True, data=detail)
