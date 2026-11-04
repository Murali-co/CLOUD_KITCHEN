from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import StaffContext, get_current_kitchen_staff, require_kitchen_manager
from app.db.database import get_db
from app.models.inventory import MovementType
from app.schemas.common import PaginatedResponse, PaginationMeta, StandardResponse
from app.schemas.inventory import (
    IngredientCreate,
    IngredientOut,
    IngredientUpdate,
    InventoryItemOut,
    InventoryMovementOut,
    InventoryReorderUpdate,
    LowStockAlertOut,
    StockAdjustmentRequest,
    StockInRequest,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/kitchen", tags=["Kitchen Inventory"])


# ---------------------------------------------------------
# Master Ingredients Catalog
# ---------------------------------------------------------
@router.get("/ingredients", response_model=StandardResponse[List[IngredientOut]])
def list_ingredients(
    category: Optional[str] = Query(None, description="Filter by ingredient category"),
    search: Optional[str] = Query(None, description="Search ingredient names"),
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Lists raw culinary ingredients available in the system catalog."""
    items = InventoryService.list_ingredients(db, category=category, search=search)
    return StandardResponse(success=True, message="Ingredients retrieved", data=items)


@router.post("/ingredients", response_model=StandardResponse[IngredientOut], status_code=status.HTTP_201_CREATED)
def create_ingredient(
    data: IngredientCreate,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Registers a new ingredient and initializes local kitchen inventory tracking."""
    item = InventoryService.create_ingredient(
        db, data=data, kitchen_id=staff_ctx.kitchen_id, user_id=staff_ctx.user.user_id
    )
    return StandardResponse(success=True, message="Ingredient created successfully", data=item)


@router.put("/ingredients/{ingredient_id}", response_model=StandardResponse[IngredientOut])
def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    staff_ctx: StaffContext = Depends(require_kitchen_manager),
    db: Session = Depends(get_db),
):
    """Updates master ingredient specification (Kitchen Manager only)."""
    updated = InventoryService.update_ingredient(db, ingredient_id=ingredient_id, data=data)
    return StandardResponse(success=True, message="Ingredient updated successfully", data=updated)


# ---------------------------------------------------------
# Inventory Stock Balances (Per Kitchen)
# ---------------------------------------------------------
@router.get("/inventory", response_model=StandardResponse[List[InventoryItemOut]])
def get_kitchen_inventory(
    low_stock_only: bool = Query(False, description="Filter to only low-stock items"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search ingredient name"),
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns on-hand stock quantities and reorder thresholds for this kitchen facility."""
    items = InventoryService.get_kitchen_inventory(
        db=db,
        kitchen_id=staff_ctx.kitchen_id,
        low_stock_only=low_stock_only,
        category=category,
        search=search,
    )
    return StandardResponse(success=True, message="Kitchen inventory balances retrieved", data=items)


@router.get("/inventory/low-stock", response_model=StandardResponse[List[LowStockAlertOut]])
def get_low_stock_alerts(
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns ingredients whose current stock is at or below their configured reorder level."""
    alerts = InventoryService.get_low_stock_alerts(db, staff_ctx.kitchen_id)
    return StandardResponse(success=True, message="Low-stock alerts retrieved", data=alerts)


@router.get("/inventory/movements", response_model=StandardResponse[PaginatedResponse[InventoryMovementOut]])
def list_inventory_movements(
    ingredient_id: Optional[int] = Query(None),
    movement_type: Optional[MovementType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Returns an immutable audit log of all stock increases, deductions, and recipe consumptions."""
    skip = (page - 1) * page_size
    items, total = InventoryService.list_movements(
        db=db,
        kitchen_id=staff_ctx.kitchen_id,
        ingredient_id=ingredient_id,
        movement_type=movement_type,
        skip=skip,
        limit=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return StandardResponse(
        success=True,
        message="Inventory movements retrieved",
        data=PaginatedResponse(
            items=items,
            meta=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
    )


@router.get("/inventory/{ingredient_id}", response_model=StandardResponse[InventoryItemOut])
def get_inventory_item(
    ingredient_id: int,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Retrieves on-hand stock balance for a specific ingredient."""
    item = InventoryService.get_inventory_item(db, staff_ctx.kitchen_id, ingredient_id)
    return StandardResponse(success=True, message="Inventory item retrieved", data=item)


@router.patch("/inventory/{ingredient_id}", response_model=StandardResponse[InventoryItemOut])
def update_reorder_level(
    ingredient_id: int,
    data: InventoryReorderUpdate,
    staff_ctx: StaffContext = Depends(require_kitchen_manager),
    db: Session = Depends(get_db),
):
    """Updates the reorder threshold for an ingredient (Kitchen Manager only)."""
    updated = InventoryService.update_reorder_level(
        db=db,
        kitchen_id=staff_ctx.kitchen_id,
        ingredient_id=ingredient_id,
        reorder_level=data.reorder_level,
    )
    return StandardResponse(success=True, message="Reorder level updated successfully", data=updated)


# ---------------------------------------------------------
# Stock Movements (Stock In & Audit Adjustments)
# ---------------------------------------------------------
@router.post("/inventory/stock-in", response_model=StandardResponse[InventoryMovementOut])
def record_stock_in(
    data: StockInRequest,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """Records receiving of culinary raw materials with positive quantity and unit cost."""
    movement = InventoryService.stock_in(
        db=db,
        kitchen_id=staff_ctx.kitchen_id,
        user_id=staff_ctx.user.user_id,
        data=data,
    )
    return StandardResponse(success=True, message="Stock-in recorded successfully", data=movement)


@router.post("/inventory/stock-adjustment", response_model=StandardResponse[InventoryMovementOut])
def record_stock_adjustment(
    data: StockAdjustmentRequest,
    staff_ctx: StaffContext = Depends(get_current_kitchen_staff),
    db: Session = Depends(get_db),
):
    """
    Records an inventory adjustment (spoilage, audit count, damage).
    Strictly forbids adjustments resulting in negative on-hand inventory.
    """
    movement = InventoryService.stock_adjustment(
        db=db,
        kitchen_id=staff_ctx.kitchen_id,
        user_id=staff_ctx.user.user_id,
        data=data,
    )
    return StandardResponse(success=True, message="Stock adjustment applied successfully", data=movement)
