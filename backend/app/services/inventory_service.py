from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventory import (
    Ingredient,
    Inventory,
    InventoryMovement,
    MovementType,
    UnitOfMeasure,
)
from app.models.kitchen import MenuItem
from app.models.order import Order
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.kitchen_repo import MenuRepository
from app.schemas.inventory import (
    IngredientCreate,
    IngredientUpdate,
    InventoryItemOut,
    InventoryMovementOut,
    LowStockAlertOut,
    RecipeDetailOut,
    RecipeItemOut,
    RecipeUpdatePayload,
    StockAdjustmentRequest,
    StockInRequest,
)


class InventoryService:
    @staticmethod
    def list_ingredients(
        db: Session, category: Optional[str] = None, search: Optional[str] = None
    ) -> List[Ingredient]:
        return InventoryRepository.get_ingredients(db, category=category, search=search)

    @staticmethod
    def create_ingredient(
        db: Session, data: IngredientCreate, kitchen_id: int, user_id: int
    ) -> Ingredient:
        existing = InventoryRepository.get_ingredient_by_name(db, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An ingredient named '{data.name}' already exists in the catalog",
            )

        ingredient = InventoryRepository.create_ingredient(
            db=db,
            name=data.name,
            category=data.category,
            unit_of_measure=data.unit_of_measure,
        )

        # Initialize kitchen inventory balance
        inv = InventoryRepository.create_or_get_inventory(
            db=db,
            kitchen_id=kitchen_id,
            ingredient_id=ingredient.ingredient_id,
            initial_stock=data.initial_stock or Decimal("0.000"),
            reorder_level=data.reorder_level or Decimal("5.000"),
        )

        if data.initial_stock and data.initial_stock > Decimal("0.000"):
            InventoryRepository.record_movement(
                db=db,
                kitchen_id=kitchen_id,
                ingredient_id=ingredient.ingredient_id,
                movement_type=MovementType.RESTOCK,
                quantity_delta=data.initial_stock,
                notes="Initial stock upon ingredient creation",
                recorded_by_user_id=user_id,
            )

        db.commit()
        db.refresh(ingredient)
        return ingredient

    @staticmethod
    def update_ingredient(
        db: Session, ingredient_id: int, data: IngredientUpdate
    ) -> Ingredient:
        ingredient = InventoryRepository.get_ingredient_by_id(db, ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found",
            )

        if data.name and data.name.strip().lower() != ingredient.name.lower():
            dup = InventoryRepository.get_ingredient_by_name(db, data.name)
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An ingredient with name '{data.name}' already exists",
                )

        updated = InventoryRepository.update_ingredient(
            db=db,
            ingredient=ingredient,
            name=data.name,
            category=data.category,
            unit_of_measure=data.unit_of_measure,
        )
        db.commit()
        db.refresh(updated)
        return updated

    @staticmethod
    def get_kitchen_inventory(
        db: Session,
        kitchen_id: int,
        low_stock_only: bool = False,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[InventoryItemOut]:
        items = InventoryRepository.get_kitchen_inventory(
            db=db,
            kitchen_id=kitchen_id,
            low_stock_only=low_stock_only,
            category=category,
            search=search,
        )
        result = []
        for itm in items:
            is_low = itm.current_stock <= itm.reorder_level
            result.append(
                InventoryItemOut(
                    inventory_id=itm.inventory_id,
                    kitchen_id=itm.kitchen_id,
                    ingredient_id=itm.ingredient_id,
                    ingredient_name=itm.ingredient.name,
                    category=itm.ingredient.category,
                    unit_of_measure=itm.ingredient.unit_of_measure,
                    current_stock=itm.current_stock,
                    reorder_level=itm.reorder_level,
                    is_low_stock=is_low,
                    last_restocked_at=itm.last_restocked_at,
                    created_at=itm.created_at,
                    updated_at=itm.updated_at,
                )
            )
        return result

    @staticmethod
    def get_inventory_item(
        db: Session, kitchen_id: int, ingredient_id: int
    ) -> InventoryItemOut:
        item = InventoryRepository.get_inventory_item(db, kitchen_id, ingredient_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient inventory record not found for this kitchen",
            )
        return InventoryItemOut(
            inventory_id=item.inventory_id,
            kitchen_id=item.kitchen_id,
            ingredient_id=item.ingredient_id,
            ingredient_name=item.ingredient.name,
            category=item.ingredient.category,
            unit_of_measure=item.ingredient.unit_of_measure,
            current_stock=item.current_stock,
            reorder_level=item.reorder_level,
            is_low_stock=item.current_stock <= item.reorder_level,
            last_restocked_at=item.last_restocked_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def update_reorder_level(
        db: Session, kitchen_id: int, ingredient_id: int, reorder_level: Decimal
    ) -> InventoryItemOut:
        item = InventoryRepository.get_inventory_item(db, kitchen_id, ingredient_id)
        if not item:
            # Create if missing
            item = InventoryRepository.create_or_get_inventory(
                db, kitchen_id, ingredient_id, reorder_level=reorder_level
            )
        item.reorder_level = reorder_level
        db.commit()
        db.refresh(item)
        return InventoryService.get_inventory_item(db, kitchen_id, ingredient_id)

    @staticmethod
    def stock_in(
        db: Session, kitchen_id: int, user_id: int, data: StockInRequest
    ) -> InventoryMovementOut:
        ingredient = InventoryRepository.get_ingredient_by_id(db, data.ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient ID {data.ingredient_id} does not exist",
            )

        # Lock inventory row for atomic stock update
        inv = InventoryRepository.get_inventory_item_for_update(db, kitchen_id, data.ingredient_id)
        if not inv:
            inv = InventoryRepository.create_or_get_inventory(
                db, kitchen_id, data.ingredient_id, initial_stock=Decimal("0.000")
            )
            db.flush()
            inv = InventoryRepository.get_inventory_item_for_update(db, kitchen_id, data.ingredient_id)

        inv.current_stock += data.quantity
        inv.last_restocked_at = datetime.utcnow()

        movement = InventoryRepository.record_movement(
            db=db,
            kitchen_id=kitchen_id,
            ingredient_id=data.ingredient_id,
            movement_type=MovementType.RESTOCK,
            quantity_delta=data.quantity,
            unit_cost=data.unit_cost,
            notes=data.notes or "Manual Stock In",
            recorded_by_user_id=user_id,
        )

        db.commit()
        db.refresh(movement)

        return InventoryMovementOut(
            movement_id=movement.movement_id,
            kitchen_id=movement.kitchen_id,
            ingredient_id=movement.ingredient_id,
            ingredient_name=ingredient.name,
            unit_of_measure=ingredient.unit_of_measure,
            movement_type=movement.movement_type,
            quantity_delta=movement.quantity_delta,
            unit_cost=movement.unit_cost,
            reference_order_id=movement.reference_order_id,
            notes=movement.notes,
            recorded_by_user_id=movement.recorded_by_user_id,
            recorded_by_name=movement.recorded_by_user.first_name if movement.recorded_by_user else None,
            created_at=movement.created_at,
        )

    @staticmethod
    def stock_adjustment(
        db: Session, kitchen_id: int, user_id: int, data: StockAdjustmentRequest
    ) -> InventoryMovementOut:
        ingredient = InventoryRepository.get_ingredient_by_id(db, data.ingredient_id)
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient ID {data.ingredient_id} does not exist",
            )

        if data.quantity_delta == Decimal("0.000"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment quantity delta must be non-zero",
            )

        inv = InventoryRepository.get_inventory_item_for_update(db, kitchen_id, data.ingredient_id)
        if not inv:
            inv = InventoryRepository.create_or_get_inventory(
                db, kitchen_id, data.ingredient_id, initial_stock=Decimal("0.000")
            )
            db.flush()
            inv = InventoryRepository.get_inventory_item_for_update(db, kitchen_id, data.ingredient_id)

        # Enforce zero negative stock constraint
        new_stock = inv.current_stock + data.quantity_delta
        if new_stock < Decimal("0.000"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Adjustment would lead to negative stock balance. "
                    f"Current stock: {inv.current_stock} {ingredient.unit_of_measure.value}, "
                    f"Requested delta: {data.quantity_delta}"
                ),
            )

        inv.current_stock = new_stock

        movement = InventoryRepository.record_movement(
            db=db,
            kitchen_id=kitchen_id,
            ingredient_id=data.ingredient_id,
            movement_type=data.movement_type,
            quantity_delta=data.quantity_delta,
            notes=data.notes,
            recorded_by_user_id=user_id,
        )

        db.commit()
        db.refresh(movement)

        return InventoryMovementOut(
            movement_id=movement.movement_id,
            kitchen_id=movement.kitchen_id,
            ingredient_id=movement.ingredient_id,
            ingredient_name=ingredient.name,
            unit_of_measure=ingredient.unit_of_measure,
            movement_type=movement.movement_type,
            quantity_delta=movement.quantity_delta,
            unit_cost=movement.unit_cost,
            reference_order_id=movement.reference_order_id,
            notes=movement.notes,
            recorded_by_user_id=movement.recorded_by_user_id,
            recorded_by_name=movement.recorded_by_user.first_name if movement.recorded_by_user else None,
            created_at=movement.created_at,
        )

    @staticmethod
    def list_movements(
        db: Session,
        kitchen_id: int,
        ingredient_id: Optional[int] = None,
        movement_type: Optional[MovementType] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[InventoryMovementOut], int]:
        movements, total = InventoryRepository.get_movements(
            db=db,
            kitchen_id=kitchen_id,
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            skip=skip,
            limit=limit,
        )
        out = []
        for m in movements:
            out.append(
                InventoryMovementOut(
                    movement_id=m.movement_id,
                    kitchen_id=m.kitchen_id,
                    ingredient_id=m.ingredient_id,
                    ingredient_name=m.ingredient.name if m.ingredient else f"ID {m.ingredient_id}",
                    unit_of_measure=m.ingredient.unit_of_measure if m.ingredient else UnitOfMeasure.PIECE,
                    movement_type=m.movement_type,
                    quantity_delta=m.quantity_delta,
                    unit_cost=m.unit_cost,
                    reference_order_id=m.reference_order_id,
                    notes=m.notes,
                    recorded_by_user_id=m.recorded_by_user_id,
                    recorded_by_name=m.recorded_by_user.first_name if m.recorded_by_user else None,
                    created_at=m.created_at,
                )
            )
        return out, total

    # -----------------------------------------------------
    # Recipe Management (Bill of Materials)
    # -----------------------------------------------------
    @staticmethod
    def get_recipe(
        db: Session, kitchen_id: int, menu_item_id: int
    ) -> RecipeDetailOut:
        item = MenuRepository.get_by_id(db, menu_item_id)
        if not item or item.kitchen_id != kitchen_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item ID {menu_item_id} does not belong to your kitchen facility",
            )

        recipe_entries = InventoryRepository.get_recipe(db, menu_item_id)
        ingredients_out = [
            RecipeItemOut(
                ingredient_id=r.ingredient_id,
                ingredient_name=r.ingredient.name,
                category=r.ingredient.category,
                quantity_required=r.quantity_required,
                unit_of_measure=r.unit_of_measure,
            )
            for r in recipe_entries
        ]

        return RecipeDetailOut(
            menu_item_id=item.menu_item_id,
            menu_item_name=item.name,
            kitchen_id=item.kitchen_id,
            ingredients=ingredients_out,
        )

    @staticmethod
    def update_recipe(
        db: Session, kitchen_id: int, menu_item_id: int, payload: RecipeUpdatePayload
    ) -> RecipeDetailOut:
        item = MenuRepository.get_by_id(db, menu_item_id)
        if not item or item.kitchen_id != kitchen_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item ID {menu_item_id} does not belong to your kitchen facility",
            )

        # Validate ingredient IDs existence
        validated_entries = []
        for ing in payload.ingredients:
            db_ing = InventoryRepository.get_ingredient_by_id(db, ing.ingredient_id)
            if not db_ing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ingredient ID {ing.ingredient_id} does not exist",
                )
            if ing.quantity_required <= Decimal("0.000"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity required for ingredient '{db_ing.name}' must be positive",
                )
            validated_entries.append(
                {
                    "ingredient_id": ing.ingredient_id,
                    "quantity_required": ing.quantity_required,
                    "unit_of_measure": ing.unit_of_measure,
                }
            )

        InventoryRepository.update_recipe(db, menu_item_id, validated_entries)
        db.commit()

        return InventoryService.get_recipe(db, kitchen_id, menu_item_id)

    # -----------------------------------------------------
    # Automatic Inventory Deduction on Order Preparation
    # -----------------------------------------------------
    @staticmethod
    def deduct_inventory_for_order(
        db: Session, order: Order, acting_user_id: int
    ) -> bool:
        """
        Transactional, recipe-based stock deduction executed when an order is transitioned to PREPARING.
        - Employs row locking (SELECT ... FOR UPDATE).
        - Idempotent: checks for prior CONSUMPTION movements for this reference_order_id.
        - Strict rollback on stock deficits: raises HTTP 400 if any ingredient has insufficient stock.
        """
        # Idempotency check: avoid double-deductions if status was clicked repeatedly
        if InventoryRepository.has_order_consumption(db, order.order_id):
            return True

        # Aggregate total ingredient requirements across all ordered dishes
        needed_quantities: Dict[int, Decimal] = defaultdict(lambda: Decimal("0.000"))
        ingredient_map: Dict[int, str] = {}

        for item in order.order_items:
            recipe_items = InventoryRepository.get_recipe(db, item.menu_item_id)
            for r in recipe_items:
                qty_for_line = r.quantity_required * Decimal(item.quantity)
                needed_quantities[r.ingredient_id] += qty_for_line
                ingredient_map[r.ingredient_id] = r.ingredient.name

        # If dishes have no recipes configured, skip safely
        if not needed_quantities:
            return True

        # Phase 1: Lock rows and validate sufficiency
        for ing_id, required_qty in needed_quantities.items():
            inv = InventoryRepository.get_inventory_item_for_update(db, order.kitchen_id, ing_id)
            if not inv or inv.current_stock < required_qty:
                ing_name = ingredient_map.get(ing_id, f"ID {ing_id}")
                available = inv.current_stock if inv else Decimal("0.000")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Cannot start preparation: Insufficient stock for ingredient '{ing_name}'. "
                        f"Required: {required_qty}, Available on-hand: {available}"
                    ),
                )

        # Phase 2: Deduct stock and record CONSUMPTION journal entries
        for ing_id, required_qty in needed_quantities.items():
            inv = InventoryRepository.get_inventory_item(db, order.kitchen_id, ing_id)
            inv.current_stock -= required_qty

            InventoryRepository.record_movement(
                db=db,
                kitchen_id=order.kitchen_id,
                ingredient_id=ing_id,
                movement_type=MovementType.CONSUMPTION,
                quantity_delta=-required_qty,
                reference_order_id=order.order_id,
                notes=f"Auto recipe consumption for Order #{order.order_number}",
                recorded_by_user_id=acting_user_id,
            )

        return True

    # -----------------------------------------------------
    # Low-Stock Alerts
    # -----------------------------------------------------
    @staticmethod
    def get_low_stock_alerts(db: Session, kitchen_id: int) -> List[LowStockAlertOut]:
        items = InventoryRepository.get_kitchen_inventory(
            db=db, kitchen_id=kitchen_id, low_stock_only=True
        )
        alerts = []
        for itm in items:
            deficit = max(Decimal("0.000"), itm.reorder_level - itm.current_stock)
            suggested = max(
                itm.reorder_level * Decimal("2.0") - itm.current_stock,
                Decimal("1.000"),
            )
            alerts.append(
                LowStockAlertOut(
                    inventory_id=itm.inventory_id,
                    ingredient_id=itm.ingredient_id,
                    ingredient_name=itm.ingredient.name,
                    category=itm.ingredient.category,
                    current_stock=itm.current_stock,
                    reorder_level=itm.reorder_level,
                    unit_of_measure=itm.ingredient.unit_of_measure,
                    deficit=deficit,
                    suggested_replenishment=suggested,
                )
            )
        return alerts
