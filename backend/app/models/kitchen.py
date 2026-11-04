from datetime import time
from typing import List, Optional
from decimal import Decimal
import enum
from sqlalchemy import (
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, BigIntPK


class OperatingStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class Kitchen(Base, TimestampMixin):
    __tablename__ = "kitchen"

    kitchen_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)
    operating_status: Mapped[OperatingStatus] = mapped_column(Enum(OperatingStatus), default=OperatingStatus.ACTIVE, nullable=False, index=True)
    opening_time: Mapped[time] = mapped_column(Time, default=time(8, 0, 0), nullable=False)
    closing_time: Mapped[time] = mapped_column(Time, default=time(23, 0, 0), nullable=False)
    max_active_orders: Mapped[int] = mapped_column(default=50, nullable=False)

    staff_members: Mapped[List["Staff"]] = relationship("Staff", back_populates="kitchen")
    menu_items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="kitchen")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="kitchen")
    inventories: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="kitchen")
    inventory_movements: Mapped[List["InventoryMovement"]] = relationship("InventoryMovement", back_populates="kitchen")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="kitchen")


class Category(Base, TimestampMixin):
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    menu_items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="category")


class MenuItem(Base, TimestampMixin):
    __tablename__ = "menu_item"

    __table_args__ = (
        UniqueConstraint("kitchen_id", "name", name="uk_kitchen_menu_item"),
    )

    menu_item_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    kitchen_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kitchen.kitchen_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("category.category_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    cuisine_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("cuisine.cuisine_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    preparation_time_minutes: Mapped[int] = mapped_column(SmallInteger, default=15, nullable=False)
    calories: Mapped[Optional[int]] = mapped_column(nullable=True)

    kitchen: Mapped["Kitchen"] = relationship("Kitchen", back_populates="menu_items")
    category: Mapped["Category"] = relationship("Category", back_populates="menu_items")
    cuisine: Mapped[Optional["Cuisine"]] = relationship("Cuisine", back_populates="menu_items")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="menu_item")
    menu_item_ingredients: Mapped[List["MenuItemIngredient"]] = relationship("MenuItemIngredient", back_populates="menu_item", cascade="all, delete-orphan")
