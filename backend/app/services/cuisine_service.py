from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.cuisine_repo import CuisineRepository
from app.schemas.cuisine import CuisineDetailResponse, CuisineResponse


class CuisineService:
    @staticmethod
    def list_cuisines(
        db: Session,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[CuisineResponse]:
        cuisines = CuisineRepository.get_all_active(db, skip=skip, limit=limit)
        return [CuisineResponse.model_validate(c) for c in cuisines]

    @staticmethod
    def get_cuisine(db: Session, cuisine_id: int) -> CuisineDetailResponse:
        cuisine = CuisineRepository.get_by_id(db, cuisine_id)
        if not cuisine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cuisine #{cuisine_id} not found",
            )
        count = CuisineRepository.get_item_count(db, cuisine_id)
        detail = CuisineDetailResponse.model_validate(cuisine)
        detail.item_count = count
        return detail

    @staticmethod
    def get_cuisine_by_slug(db: Session, slug: str) -> CuisineDetailResponse:
        cuisine = CuisineRepository.get_by_slug(db, slug)
        if not cuisine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cuisine '{slug}' not found",
            )
        count = CuisineRepository.get_item_count(db, cuisine.cuisine_id)
        detail = CuisineDetailResponse.model_validate(cuisine)
        detail.item_count = count
        return detail
