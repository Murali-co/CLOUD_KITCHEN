from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import enum
from pydantic import BaseModel, Field, ConfigDict

from app.models.inventory import UnitOfMeasure, MovementType


# ---------------------------------------------------------
# Ingredient Master Schemas
# ---------------------------------------------------------
class IngredientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    unit_of_measure: UnitOfMeasure
    initial_stock: Optional[Decimal] = Field(default=Decimal("0.000"), ge=Decimal("0.000"))
    reorder_level: Optional[Decimal] = Field(default=Decimal("5.000"), ge=Decimal("0.000"))


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[UnitOfMeasure] = None


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient_id: int
    name: str
    category: Optional[str] = None
    unit_of_measure: UnitOfMeasure
    created_at: datetime


# ---------------------------------------------------------
# Inventory Stock Level Schemas
# ---------------------------------------------------------
class InventoryItemOut(BaseModel):
    inventory_id: int
    kitchen_id: int
    ingredient_id: int
    ingredient_name: str
    category: Optional[str] = None
    unit_of_measure: UnitOfMeasure
    current_stock: Decimal
    reorder_level: Decimal
    is_low_stock: bool
    last_restocked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class InventoryReorderUpdate(BaseModel):
    reorder_level: Decimal = Field(..., ge=Decimal("0.000"))


# ---------------------------------------------------------
# Stock In & Stock Adjustment Schemas
# ---------------------------------------------------------
class StockInRequest(BaseModel):
    ingredient_id: int
    quantity: Decimal = Field(..., gt=Decimal("0.000"), description="Positive amount to add to on-hand inventory")
    unit_cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    notes: Optional[str] = Field(None, max_length=500)


class StockAdjustmentRequest(BaseModel):
    ingredient_id: int
    quantity_delta: Decimal = Field(..., description="Quantity delta. Positive to add, negative to deduct")
    movement_type: MovementType = Field(default=MovementType.AUDIT_ADJUSTMENT)
    notes: str = Field(..., min_length=3, max_length=500, description="Audit reason for stock adjustment")


class InventoryMovementOut(BaseModel):
    movement_id: int
    kitchen_id: int
    ingredient_id: int
    ingredient_name: str
    unit_of_measure: UnitOfMeasure
    movement_type: MovementType
    quantity_delta: Decimal
    unit_cost: Optional[Decimal] = None
    reference_order_id: Optional[int] = None
    notes: Optional[str] = None
    recorded_by_user_id: Optional[int] = None
    recorded_by_name: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------
# Recipe Management Schemas (Bill of Materials)
# ---------------------------------------------------------
class RecipeItemInput(BaseModel):
    ingredient_id: int
    quantity_required: Decimal = Field(..., gt=Decimal("0.000"), description="Quantity consumed per serving")
    unit_of_measure: UnitOfMeasure


class RecipeUpdatePayload(BaseModel):
    ingredients: List[RecipeItemInput] = Field(..., description="Complete list of recipe ingredients")


class RecipeItemOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    category: Optional[str] = None
    quantity_required: Decimal
    unit_of_measure: UnitOfMeasure


class RecipeDetailOut(BaseModel):
    menu_item_id: int
    menu_item_name: str
    kitchen_id: int
    ingredients: List[RecipeItemOut]


# ---------------------------------------------------------
# Low Stock Alert Schema
# ---------------------------------------------------------
class LowStockAlertOut(BaseModel):
    inventory_id: int
    ingredient_id: int
    ingredient_name: str
    category: Optional[str] = None
    current_stock: Decimal
    reorder_level: Decimal
    unit_of_measure: UnitOfMeasure
    deficit: Decimal
    suggested_replenishment: Decimal
