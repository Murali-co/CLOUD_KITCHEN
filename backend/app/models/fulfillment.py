from datetime import datetime
from typing import List, Optional
from decimal import Decimal
import enum
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, BigIntPK


class DeliveryStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class Delivery(Base, TimestampMixin):
    __tablename__ = "delivery"

    delivery_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="RESTRICT", onupdate="CASCADE"), unique=True, nullable=False)
    delivery_person_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("delivery_person.delivery_person_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.ASSIGNED, nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    delivery_otp: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_signature_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="delivery")
    delivery_person: Mapped["DeliveryPerson"] = relationship("DeliveryPerson", back_populates="deliveries")


class Coupon(Base, TimestampMixin):
    __tablename__ = "coupon"

    coupon_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    usage_limit_per_user: Mapped[int] = mapped_column(default=1, nullable=False)
    total_usage_limit: Mapped[int] = mapped_column(default=1000, nullable=False)
    current_usage_count: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="coupon")
    usages: Mapped[List["CouponUsage"]] = relationship("CouponUsage", back_populates="coupon")


class CouponUsage(Base):
    __tablename__ = "coupon_usage"

    usage_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    coupon_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("coupon.coupon_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customer.customer_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    discount_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    coupon: Mapped["Coupon"] = relationship("Coupon", back_populates="usages")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="coupon_usages")
    order: Mapped["Order"] = relationship("Order", back_populates="coupon_usage")


class Review(Base, TimestampMixin):
    __tablename__ = "review"

    review_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.order_id", ondelete="RESTRICT", onupdate="CASCADE"), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customer.customer_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    kitchen_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kitchen.kitchen_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_reply: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="review")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="reviews")
    kitchen: Mapped["Kitchen"] = relationship("Kitchen", back_populates="reviews")
