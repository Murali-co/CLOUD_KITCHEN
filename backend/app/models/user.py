from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal
import enum
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, BigIntPK


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"
    KITCHEN_STAFF = "KITCHEN_STAFF"
    DELIVERY_PERSON = "DELIVERY_PERSON"


class DietaryPreference(str, enum.Enum):
    ALL = "ALL"
    VEGETARIAN = "VEGETARIAN"
    VEGAN = "VEGAN"
    HALAL = "HALAL"
    GLUTEN_FREE = "GLUTEN_FREE"


class StaffRole(str, enum.Enum):
    KITCHEN_MANAGER = "KITCHEN_MANAGER"
    HEAD_CHEF = "HEAD_CHEF"
    LINE_COOK = "LINE_COOK"
    PACKER = "PACKER"
    INVENTORY_CONTROLLER = "INVENTORY_CONTROLLER"


class ShiftTiming(str, enum.Enum):
    MORNING = "MORNING"
    EVENING = "EVENING"
    NIGHT = "NIGHT"
    ROTATING = "ROTATING"


class VehicleType(str, enum.Enum):
    MOTORCYCLE = "MOTORCYCLE"
    SCOOTER = "SCOOTER"
    BICYCLE = "BICYCLE"
    ELECTRIC_VEHICLE = "ELECTRIC_VEHICLE"


class DeliveryPersonStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_DELIVERY = "ON_DELIVERY"
    OFF_DUTY = "OFF_DUTY"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 1:1 Polymorphic Sub-class links
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    staff: Mapped[Optional["Staff"]] = relationship("Staff", back_populates="user", uselist=False, cascade="all, delete-orphan")
    delivery_person: Mapped[Optional["DeliveryPerson"]] = relationship("DeliveryPerson", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.user_id} email={self.email} role={self.role}>"


class Customer(Base, TimestampMixin):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    loyalty_points: Mapped[int] = mapped_column(default=0, nullable=False)
    dietary_preference: Mapped[DietaryPreference] = mapped_column(Enum(DietaryPreference), default=DietaryPreference.ALL, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="customer")
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="customer", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")
    coupon_usages: Mapped[List["CouponUsage"]] = relationship("CouponUsage", back_populates="customer")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="customer")


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    staff_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    kitchen_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("kitchen.kitchen_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True)
    staff_role: Mapped[StaffRole] = mapped_column(Enum(StaffRole), nullable=False)
    shift_timing: Mapped[ShiftTiming] = mapped_column(Enum(ShiftTiming), default=ShiftTiming.MORNING, nullable=False)
    hired_date: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="staff")
    kitchen: Mapped["Kitchen"] = relationship("Kitchen", back_populates="staff_members")


class DeliveryPerson(Base, TimestampMixin):
    __tablename__ = "delivery_person"

    delivery_person_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    vehicle_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    driving_license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    current_status: Mapped[DeliveryPersonStatus] = mapped_column(Enum(DeliveryPersonStatus), default=DeliveryPersonStatus.AVAILABLE, nullable=False, index=True)
    current_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 8), nullable=True)
    current_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(11, 8), nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("5.00"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="delivery_person")
    deliveries: Mapped[List["Delivery"]] = relationship("Delivery", back_populates="delivery_person")
