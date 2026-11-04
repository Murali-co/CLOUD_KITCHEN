from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.inventory import (
    Ingredient,
    Inventory,
    InventoryMovement,
    MenuItemIngredient,
    MovementType,
    UnitOfMeasure,
)
from app.models.kitchen import MenuItem


class InventoryRepository:
    # -----------------------------------------------------
    # Master Ingredient Catalog
    # -----------------------------------------------------
    @staticmethod
    def get_ingredients(
        db: Session, category: Optional[str] = None, search: Optional[str] = None
    ) -> List[Ingredient]:
        query = db.query(Ingredient)
        if category:
            query = query.filter(Ingredient.category == category)
        if search:
            query = query.filter(Ingredient.name.ilike(f"%{search.strip()}%"))
        return query.order_by(Ingredient.name.asc()).all()

    @staticmethod
    def get_ingredient_by_id(db: Session, ingredient_id: int) -> Optional[Ingredient]:
        return db.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()

    @staticmethod
    def get_ingredient_by_name(db: Session, name: str) -> Optional[Ingredient]:
        return db.query(Ingredient).filter(func.lower(Ingredient.name) == func.lower(name.strip())).first()

    @staticmethod
    def create_ingredient(
        db: Session,
        name: str,
        category: Optional[str],
        unit_of_measure: UnitOfMeasure,
    ) -> Ingredient:
        ingredient = Ingredient(
            name=name.strip(),
            category=category.strip() if category else None,
            unit_of_measure=unit_of_measure,
        )
        db.add(ingredient)
        db.flush()
        return ingredient

    @staticmethod
    def update_ingredient(
        db: Session,
        ingredient: Ingredient,
        name: Optional[str] = None,
        category: Optional[str] = None,
        unit_of_measure: Optional[UnitOfMeasure] = None,
    ) -> Ingredient:
        if name:
            ingredient.name = name.strip()
        if category is not None:
            ingredient.category = category.strip() if category else None
        if unit_of_measure:
            ingredient.unit_of_measure = unit_of_measure
        db.flush()
        return ingredient

    # -----------------------------------------------------
    # Inventory Balances (Per Kitchen)
    # -----------------------------------------------------
    @staticmethod
    def get_inventory_item(
        db: Session, kitchen_id: int, ingredient_id: int
    ) -> Optional[Inventory]:
        return (
            db.query(Inventory)
            .options(joinedload(Inventory.ingredient))
            .filter(
                Inventory.kitchen_id == kitchen_id,
                Inventory.ingredient_id == ingredient_id,
            )
            .first()
        )

    @staticmethod
    def get_inventory_item_for_update(
        db: Session, kitchen_id: int, ingredient_id: int
    ) -> Optional[Inventory]:
        """Locks row with SELECT ... FOR UPDATE for atomic stock mutations."""
        return (
            db.query(Inventory)
            .filter(
                Inventory.kitchen_id == kitchen_id,
                Inventory.ingredient_id == ingredient_id,
            )
            .with_for_update()
            .first()
        )

    @staticmethod
    def create_or_get_inventory(
        db: Session,
        kitchen_id: int,
        ingredient_id: int,
        initial_stock: Decimal = Decimal("0.000"),
        reorder_level: Decimal = Decimal("5.000"),
    ) -> Inventory:
        item = (
            db.query(Inventory)
            .filter(
                Inventory.kitchen_id == kitchen_id,
                Inventory.ingredient_id == ingredient_id,
            )
            .first()
        )
        if not item:
            item = Inventory(
                kitchen_id=kitchen_id,
                ingredient_id=ingredient_id,
                current_stock=initial_stock,
                reorder_level=reorder_level,
                last_restocked_at=datetime.utcnow() if initial_stock > 0 else None,
            )
            db.add(item)
            db.flush()
        return item

    @staticmethod
    def get_kitchen_inventory(
        db: Session,
        kitchen_id: int,
        low_stock_only: bool = False,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Inventory]:
        query = (
            db.query(Inventory)
            .join(Ingredient, Inventory.ingredient_id == Ingredient.ingredient_id)
            .options(joinedload(Inventory.ingredient))
            .filter(Inventory.kitchen_id == kitchen_id)
        )
        if low_stock_only:
            query = query.filter(Inventory.current_stock <= Inventory.reorder_level)
        if category:
            query = query.filter(Ingredient.category == category)
        if search:
            query = query.filter(Ingredient.name.ilike(f"%{search.strip()}%"))

        return query.order_by(Ingredient.name.asc()).all()

    @staticmethod
    def update_reorder_level(
        db: Session, inventory: Inventory, reorder_level: Decimal
    ) -> Inventory:
        inventory.reorder_level = reorder_level
        db.flush()
        return inventory

    @staticmethod
    def count_low_stock(db: Session, kitchen_id: int) -> int:
        return (
            db.query(func.count(Inventory.inventory_id))
            .filter(
                Inventory.kitchen_id == kitchen_id,
                Inventory.current_stock <= Inventory.reorder_level,
            )
            .scalar()
            or 0
        )

    # -----------------------------------------------------
    # Stock Movements & Audit Journal
    # -----------------------------------------------------
    @staticmethod
    def record_movement(
        db: Session,
        kitchen_id: int,
        ingredient_id: int,
        movement_type: MovementType,
        quantity_delta: Decimal,
        unit_cost: Optional[Decimal] = None,
        reference_order_id: Optional[int] = None,
        notes: Optional[str] = None,
        recorded_by_user_id: Optional[int] = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            kitchen_id=kitchen_id,
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            quantity_delta=quantity_delta,
            unit_cost=unit_cost,
            reference_order_id=reference_order_id,
            notes=notes,
            recorded_by_user_id=recorded_by_user_id,
        )
        db.add(movement)
        db.flush()
        return movement

    @staticmethod
    def get_movements(
        db: Session,
        kitchen_id: int,
        ingredient_id: Optional[int] = None,
        movement_type: Optional[MovementType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[InventoryMovement], int]:
        query = (
            db.query(InventoryMovement)
            .options(
                joinedload(InventoryMovement.ingredient),
                joinedload(InventoryMovement.recorded_by_user),
            )
            .filter(InventoryMovement.kitchen_id == kitchen_id)
        )
        if ingredient_id:
            query = query.filter(InventoryMovement.ingredient_id == ingredient_id)
        if movement_type:
            query = query.filter(InventoryMovement.movement_type == movement_type)

        total = query.count()
        movements = query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()
        return movements, total

    @staticmethod
    def has_order_consumption(db: Session, order_id: int) -> bool:
        """Checks if recipe consumption movements were already logged for an order."""
        return (
            db.query(InventoryMovement)
            .filter(
                InventoryMovement.reference_order_id == order_id,
                InventoryMovement.movement_type == MovementType.CONSUMPTION,
            )
            .first()
            is not None
        )

    # -----------------------------------------------------
    # Recipe Management (menu_item_ingredient)
    # -----------------------------------------------------
    @staticmethod
    def get_recipe(db: Session, menu_item_id: int) -> List[MenuItemIngredient]:
        return (
            db.query(MenuItemIngredient)
            .options(joinedload(MenuItemIngredient.ingredient))
            .filter(MenuItemIngredient.menu_item_id == menu_item_id)
            .all()
        )

    @staticmethod
    def update_recipe(
        db: Session, menu_item_id: int, ingredients: List[dict]
    ) -> List[MenuItemIngredient]:
        """Atomically replaces recipe Bill of Materials."""
        db.query(MenuItemIngredient).filter(
            MenuItemIngredient.menu_item_id == menu_item_id
        ).delete()

        new_entries = []
        for item in ingredients:
            entry = MenuItemIngredient(
                menu_item_id=menu_item_id,
                ingredient_id=item["ingredient_id"],
                quantity_required=item["quantity_required"],
                unit_of_measure=item["unit_of_measure"],
            )
            db.add(entry)
            new_entries.append(entry)

        db.flush()
        return new_entries
