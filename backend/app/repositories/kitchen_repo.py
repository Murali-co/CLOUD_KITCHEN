from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Kitchen, OperatingStatus, Category, MenuItem


class KitchenRepository:
    @staticmethod
    def get_active_kitchens(
        db: Session,
        search: Optional[str] = None,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Kitchen], int]:
        query = db.query(Kitchen).filter(Kitchen.operating_status == OperatingStatus.ACTIVE)
        if search:
            query = query.filter(Kitchen.name.ilike(f"%{search.strip()}%"))
        if city:
            query = query.filter(Kitchen.city.ilike(f"%{city.strip()}%"))
        
        total = query.count()
        kitchens = query.offset(skip).limit(limit).all()
        return kitchens, total

    @staticmethod
    def get_by_id(db: Session, kitchen_id: int) -> Optional[Kitchen]:
        return db.query(Kitchen).filter(Kitchen.kitchen_id == kitchen_id).first()

    @staticmethod
    def update_operating_status(
        db: Session,
        kitchen: Kitchen,
        operating_status: OperatingStatus,
        max_active_orders: Optional[int] = None,
    ) -> Kitchen:
        kitchen.operating_status = operating_status
        if max_active_orders is not None:
            kitchen.max_active_orders = max_active_orders
        db.flush()
        return kitchen


class CategoryRepository:
    @staticmethod
    def get_all_active(db: Session) -> List[Category]:
        return (
            db.query(Category)
            .filter(Category.is_active == True)
            .order_by(Category.display_order.asc(), Category.name.asc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.category_id == category_id).first()


class MenuRepository:
    @staticmethod
    def search_menu(
        db: Session,
        kitchen_id: Optional[int] = None,
        category_id: Optional[int] = None,
        cuisine_id: Optional[int] = None,
        search: Optional[str] = None,
        is_vegetarian: Optional[bool] = None,
        is_available: Optional[bool] = True,
        sort_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[MenuItem], int]:
        query = db.query(MenuItem)
        if kitchen_id:
            query = query.filter(MenuItem.kitchen_id == kitchen_id)
        if category_id:
            query = query.filter(MenuItem.category_id == category_id)
        if cuisine_id:
            query = query.filter(MenuItem.cuisine_id == cuisine_id)
        if search:
            query = query.filter(MenuItem.name.ilike(f"%{search.strip()}%"))
        if is_vegetarian is not None:
            query = query.filter(MenuItem.is_vegetarian == is_vegetarian)
        if is_available is not None:
            query = query.filter(MenuItem.is_available == is_available)

        if sort_by == "price_asc":
            query = query.order_by(MenuItem.base_price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(MenuItem.base_price.desc())
        else:
            query = query.order_by(MenuItem.name.asc())

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[MenuItem]:
        return db.query(MenuItem).filter(MenuItem.menu_item_id == item_id).first()

    @staticmethod
    def get_by_id_and_kitchen(db: Session, item_id: int, kitchen_id: int) -> Optional[MenuItem]:
        return (
            db.query(MenuItem)
            .filter(MenuItem.menu_item_id == item_id, MenuItem.kitchen_id == kitchen_id)
            .first()
        )

    @staticmethod
    def create_item(
        db: Session,
        kitchen_id: int,
        category_id: int,
        name: str,
        description: Optional[str],
        base_price: Decimal,
        is_vegetarian: bool,
        is_available: bool,
        preparation_time_minutes: int,
        calories: Optional[int],
    ) -> MenuItem:
        item = MenuItem(
            kitchen_id=kitchen_id,
            category_id=category_id,
            name=name.strip(),
            description=description.strip() if description else None,
            base_price=base_price,
            is_vegetarian=is_vegetarian,
            is_available=is_available,
            preparation_time_minutes=preparation_time_minutes,
            calories=calories,
        )
        db.add(item)
        db.flush()
        return item

    @staticmethod
    def update_item(
        db: Session,
        item: MenuItem,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None,
        base_price: Optional[Decimal] = None,
        is_vegetarian: Optional[bool] = None,
        is_available: Optional[bool] = None,
        preparation_time_minutes: Optional[int] = None,
        calories: Optional[int] = None,
    ) -> MenuItem:
        if name:
            item.name = name.strip()
        if category_id:
            item.category_id = category_id
        if description is not None:
            item.description = description.strip() if description else None
        if base_price is not None:
            item.base_price = base_price
        if is_vegetarian is not None:
            item.is_vegetarian = is_vegetarian
        if is_available is not None:
            item.is_available = is_available
        if preparation_time_minutes is not None:
            item.preparation_time_minutes = preparation_time_minutes
        if calories is not None:
            item.calories = calories

        db.flush()
        return item

    @staticmethod
    def update_availability(db: Session, item: MenuItem, is_available: bool) -> MenuItem:
        item.is_available = is_available
        db.flush()
        return item

