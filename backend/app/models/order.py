from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import enum
from sqlalchemy import (
    BigInteger,
    CHAR,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.base import Base, BigIntPK


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        UniqueConstraint("order_id", "kitchen_id", name="uk_orders_order_kitchen"),
        ForeignKeyConstraint(
            ["delivery_address_id", "customer_id"],
            ["address.address_id", "address.customer_id"],
            name="fk_orders_customer_address",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
    )

    order_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customer.customer_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    kitchen_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kitchen.kitchen_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    delivery_address_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    applied_coupon_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("coupon.coupon_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_delivery_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    kitchen: Mapped["Kitchen"] = relationship("Kitchen", back_populates="orders")
    delivery_address: Mapped["Address"] = relationship(
        "Address",
        primaryjoin="and_(foreign(Order.delivery_address_id) == Address.address_id, Order.customer_id == Address.customer_id)",
        back_populates="orders",
        overlaps="customer,orders",
    )
    coupon: Mapped[Optional["Coupon"]] = relationship("Coupon", back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="order")
    status_history: Mapped[List["OrderStatusHistory"]] = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    delivery: Mapped[Optional["Delivery"]] = relationship("Delivery", back_populates="order", uselist=False)
    coupon_usage: Mapped[Optional["CouponUsage"]] = relationship("CouponUsage", back_populates="order", uselist=False, cascade="all, delete-orphan")
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_item"

    order_item_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    menu_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("menu_item.menu_item_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    item_name_snapshot: Mapped[str] = mapped_column(String(150), nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    subtotal_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    customization_notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    gateway_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), default="INR", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="payments")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    history_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    previous_status: Mapped[Optional[OrderStatus]] = mapped_column(Enum(OrderStatus), nullable=True)
    new_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False, index=True)

    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
    changed_by_user: Mapped[Optional["User"]] = relationship("User")
