from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import enum
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, BigIntPK


class UnitOfMeasure(str, enum.Enum):
    KG = "KG"
    GRAM = "GRAM"
    LITER = "LITER"
    MILLILITER = "MILLILITER"
    PIECE = "PIECE"
    PACKET = "PACKET"


class MovementType(str, enum.Enum):
    RESTOCK = "RESTOCK"
    CONSUMPTION = "CONSUMPTION"
    SPOILAGE = "SPOILAGE"
    AUDIT_ADJUSTMENT = "AUDIT_ADJUSTMENT"
    RETURN = "RETURN"


class Ingredient(Base, TimestampMixin):
    __tablename__ = "ingredient"

    ingredient_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_of_measure: Mapped[UnitOfMeasure] = mapped_column(Enum(UnitOfMeasure), nullable=False)

    inventories: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="ingredient")
    movements: Mapped[List["InventoryMovement"]] = relationship("InventoryMovement", back_populates="ingredient")
    menu_item_ingredients: Mapped[List["MenuItemIngredient"]] = relationship("MenuItemIngredient", back_populates="ingredient")


class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"

    __table_args__ = (
        UniqueConstraint("kitchen_id", "ingredient_id", name="uk_kitchen_ingredient"),
    )

    inventory_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    kitchen_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kitchen.kitchen_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    ingredient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ingredient.ingredient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0.000"), nullable=False)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0.000"), nullable=False)
    last_restocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    kitchen: Mapped["Kitchen"] = relationship("Kitchen", back_populates="inventories")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="inventories")


class InventoryMovement(Base):
    __tablename__ = "inventory_movement"

    movement_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    kitchen_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kitchen.kitchen_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    ingredient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ingredient.ingredient_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    reference_order_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False, index=True)

    kitchen: Mapped["Kitchen"] = relationship("Kitchen", back_populates="inventory_movements")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="movements")
    reference_order: Mapped[Optional["Order"]] = relationship("Order")
    recorded_by_user: Mapped[Optional["User"]] = relationship("User")


class MenuItemIngredient(Base):
    __tablename__ = "menu_item_ingredient"

    menu_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("menu_item.menu_item_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ingredient.ingredient_id", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True, index=True)
    quantity_required: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_of_measure: Mapped[UnitOfMeasure] = mapped_column(Enum(UnitOfMeasure), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="menu_item_ingredients")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="menu_item_ingredients")
