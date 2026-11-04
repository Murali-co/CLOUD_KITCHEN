from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.category import CategoryResponse
from app.schemas.common import StandardResponse
from app.services.kitchen_service import MenuService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=StandardResponse[List[CategoryResponse]])
def list_categories(db: Session = Depends(get_db)):
    """Retrieves all active food categories."""
    categories = MenuService.list_categories(db)
    return StandardResponse(success=True, data=categories)
