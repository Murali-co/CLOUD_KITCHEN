from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BigIntPK


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    audit_id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    actor_user: Mapped["User"] = relationship("User", foreign_keys=[actor_user_id])

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_created", "created_at"),
    )
