from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.cuisine import Cuisine
from app.models.kitchen import MenuItem


class CuisineRepository:
    @staticmethod
    def get_all_active(
        db: Session,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Cuisine]:
        query = (
            db.query(Cuisine)
            .filter(Cuisine.is_active == True)
            .order_by(Cuisine.display_order.asc(), Cuisine.cuisine_name.asc())
        )
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_by_id(db: Session, cuisine_id: int) -> Optional[Cuisine]:
        return db.query(Cuisine).filter(Cuisine.cuisine_id == cuisine_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Cuisine]:
        return db.query(Cuisine).filter(Cuisine.cuisine_slug == slug.strip().lower()).first()

    @staticmethod
    def get_item_count(db: Session, cuisine_id: int) -> int:
        return (
            db.query(func.count(MenuItem.menu_item_id))
            .filter(MenuItem.cuisine_id == cuisine_id, MenuItem.is_available == True)
            .scalar()
            or 0
        )
