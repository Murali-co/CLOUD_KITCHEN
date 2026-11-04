from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.common import StandardResponse
from app.schemas.cuisine import CuisineDetailResponse, CuisineResponse
from app.services.cuisine_service import CuisineService

router = APIRouter(prefix="/cuisines", tags=["Cuisines"])


@router.get("", response_model=StandardResponse[List[CuisineResponse]])
def list_cuisines(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit for pagination"),
    db: Session = Depends(get_db),
):
    """Retrieves all active cuisines ordered by display order."""
    cuisines = CuisineService.list_cuisines(db, skip=skip, limit=limit)
    return StandardResponse(success=True, data=cuisines)


@router.get("/slug/{slug}", response_model=StandardResponse[CuisineDetailResponse])
def get_cuisine_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    """Retrieves cuisine details by its unique URL slug."""
    cuisine = CuisineService.get_cuisine_by_slug(db, slug)
    return StandardResponse(success=True, data=cuisine)


@router.get("/{cuisine_id}", response_model=StandardResponse[CuisineDetailResponse])
def get_cuisine(
    cuisine_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves cuisine details and active menu item count by ID."""
    cuisine = CuisineService.get_cuisine(db, cuisine_id)
    return StandardResponse(success=True, data=cuisine)
