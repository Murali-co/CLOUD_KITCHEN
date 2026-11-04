from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, BigIntPK


class Cuisine(Base, TimestampMixin):
    __tablename__ = "cuisine"

    cuisine_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    cuisine_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    cuisine_slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    cuisine_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cuisine_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)

    menu_items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="cuisine")
