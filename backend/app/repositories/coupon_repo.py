from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Coupon, CouponUsage


class CouponRepository:
    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Coupon]:
        return db.query(Coupon).filter(Coupon.code == code.upper().strip()).first()

    @staticmethod
    def get_customer_usage_count(db: Session, coupon_id: int, customer_id: int) -> int:
        return (
            db.query(CouponUsage)
            .filter(CouponUsage.coupon_id == coupon_id, CouponUsage.customer_id == customer_id)
            .count()
        )

    @staticmethod
    def record_usage(db: Session, coupon: Coupon, customer_id: int, order_id: int, discount_applied) -> CouponUsage:
        usage = CouponUsage(
            coupon_id=coupon.coupon_id,
            customer_id=customer_id,
            order_id=order_id,
            discount_applied=discount_applied,
        )
        db.add(usage)
        coupon.current_usage_count += 1
        return usage
