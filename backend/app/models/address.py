from typing import List, Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.base import Base, TimestampMixin, BigIntPK


class Address(Base, TimestampMixin):
    __tablename__ = "address"

    __table_args__ = (
        UniqueConstraint("address_id", "customer_id", name="uk_address_customer"),
    )

    address_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customer.customer_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    address_label: Mapped[str] = mapped_column(String(50), default="Home", nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="addresses")
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        primaryjoin="and_(Address.address_id == foreign(Order.delivery_address_id), Address.customer_id == Order.customer_id)",
        back_populates="delivery_address",
        overlaps="customer,orders",
    )
