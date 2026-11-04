from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.common import PaginatedResponse, StandardResponse
from app.schemas.kitchen import KitchenDetailResponse, KitchenResponse
from app.services.kitchen_service import KitchenService

router = APIRouter(prefix="/kitchens", tags=["Kitchens"])


@router.get("", response_model=StandardResponse[PaginatedResponse[KitchenResponse]])
def list_kitchens(
    search: Optional[str] = Query(None, description="Search by kitchen branch name"),
    city: Optional[str] = Query(None, description="Filter by operational municipality/city"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieves all operating cloud kitchen branches."""
    paginated = KitchenService.list_kitchens(db, search=search, city=city, page=page, page_size=page_size)
    return StandardResponse(success=True, data=paginated)


@router.get("/{kitchen_id}", response_model=StandardResponse[KitchenDetailResponse])
def get_kitchen_detail(
    kitchen_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves detailed operational info for a specific cloud kitchen branch."""
    detail = KitchenService.get_kitchen_detail(db, kitchen_id)
    return StandardResponse(success=True, data=detail)
