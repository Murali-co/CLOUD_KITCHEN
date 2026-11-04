from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Payment, PaymentStatus, PaymentMethod


class PaymentRepository:
    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.payment_id == payment_id).first()

    @staticmethod
    def get_by_reference(db: Session, reference: str) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.transaction_reference == reference).first()

    @staticmethod
    def get_latest_by_order(db: Session, order_id: int) -> Optional[Payment]:
        return (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .order_by(Payment.payment_id.desc())
            .first()
        )

    @staticmethod
    def create_payment(
        db: Session,
        order_id: int,
        payment_method: str,
        amount: Decimal,
        transaction_reference: Optional[str] = None,
        gateway_name: str = "TestGateway",
    ) -> Payment:
        pay_enum = PaymentMethod[payment_method] if payment_method in PaymentMethod.__members__ else PaymentMethod.UPI
        payment = Payment(
            order_id=order_id,
            payment_method=pay_enum,
            payment_status=PaymentStatus.PENDING,
            transaction_reference=transaction_reference,
            gateway_name=gateway_name,
            amount=amount,
            currency="INR",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def update_status(
        db: Session,
        payment: Payment,
        new_status: PaymentStatus,
        transaction_reference: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Payment:
        payment.payment_status = new_status
        if transaction_reference:
            payment.transaction_reference = transaction_reference
        if error_message:
            payment.error_message = error_message
        if new_status in (PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.REFUNDED):
            payment.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(payment)
        return payment
