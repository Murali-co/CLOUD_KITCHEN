import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.audit import AdminAuditLog
from app.models.user import User


class AuditRepository:
    @staticmethod
    def record_audit(
        db: Session,
        actor_user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AdminAuditLog:
        """
        Inserts an immutable administrative audit record.
        Strictly sanitizes details to ensure no passwords or credentials are recorded.
        """
        sanitized_details = None
        if details:
            sanitized = {}
            for k, v in details.items():
                if any(secret in k.lower() for secret in ["password", "token", "secret", "cvv", "key"]):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = v
            sanitized_details = sanitized

        entry = AdminAuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=sanitized_details,
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def get_audit_logs(
        db: Session,
        actor_user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AdminAuditLog], int]:
        query = db.query(AdminAuditLog)
        if actor_user_id:
            query = query.filter(AdminAuditLog.actor_user_id == actor_user_id)
        if entity_type:
            query = query.filter(AdminAuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AdminAuditLog.action.ilike(f"%{action}%"))

        total = query.count()
        logs = query.order_by(desc(AdminAuditLog.created_at)).offset(skip).limit(limit).all()
        return logs, total
