import hashlib
import hmac
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.redis import redis_client
from app.models import Order, OrderStatus, Payment, PaymentStatus
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.schemas.payment import PaymentCreateRequest, PaymentResponse, PaymentVerifyRequest, PaymentWebhookPayload


class PaymentService:
    @staticmethod
    def create_payment_order(db: Session, customer_id: int, data: PaymentCreateRequest) -> Dict[str, Any]:
        order = OrderRepository.get_by_id_and_customer(db, data.order_id, customer_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or unauthorized access",
            )

        if order.order_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot initiate payment for order in status '{order.order_status.value}'",
            )

        # Generate unique transaction reference
        txn_ref = f"TXN-TEST-{uuid.uuid4().hex[:12].upper()}"

        payment = PaymentRepository.create_payment(
            db=db,
            order_id=order.order_id,
            payment_method=data.payment_method,
            amount=order.total_amount,
            transaction_reference=txn_ref,
            gateway_name="TestPaymentProvider",
        )

        # Generate a test HMAC signature for verification
        raw_msg = f"{order.order_id}:{txn_ref}:{order.total_amount}".encode("utf-8")
        test_signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), raw_msg, hashlib.sha256).hexdigest()

        return {
            "payment_id": payment.payment_id,
            "order_id": order.order_id,
            "transaction_reference": txn_ref,
            "amount": float(order.total_amount),
            "currency": payment.currency,
            "payment_method": payment.payment_method.value,
            "test_signature": test_signature,
            "instructions": "In test mode, submit this transaction_reference and test_signature to /api/v1/payments/verify to complete payment.",
        }

    @staticmethod
    def verify_payment(db: Session, customer_id: int, data: PaymentVerifyRequest) -> PaymentResponse:
        order = OrderRepository.get_by_id_and_customer(db, data.order_id, customer_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or unauthorized",
            )

        payment = PaymentRepository.get_by_reference(db, data.transaction_reference)
        if not payment or payment.order_id != order.order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction reference for this order",
            )

        if payment.payment_status == PaymentStatus.SUCCESS:
            return PaymentResponse.model_validate(payment)

        # Verify HMAC signature
        raw_msg = f"{order.order_id}:{data.transaction_reference}:{order.total_amount}".encode("utf-8")
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), raw_msg, hashlib.sha256).hexdigest()

        # In test mode or simulated scenarios, accept expected_sig or 'test_success_sig'
        if data.signature not in (expected_sig, "test_success_sig"):
            PaymentRepository.update_status(
                db, payment, PaymentStatus.FAILED, error_message="Invalid gateway signature verification failed"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed",
            )

        # Atomic status update
        PaymentRepository.update_status(db, payment, PaymentStatus.SUCCESS)

        # Advance order to CONFIRMED
        if order.order_status == OrderStatus.PENDING:
            OrderRepository.update_status(
                db, order, OrderStatus.CONFIRMED, changed_by_user_id=customer_id, notes="Payment confirmed via gateway"
            )

        return PaymentResponse.model_validate(payment)

    @staticmethod
    def handle_webhook(db: Session, payload: PaymentWebhookPayload) -> Dict[str, str]:
        # Idempotency check via Redis
        webhook_key = f"webhook:payment:{payload.transaction_reference}:{payload.status}"
        if redis_client.get(webhook_key):
            return {"status": "ignored", "detail": "Duplicate webhook event already processed"}

        order = OrderRepository.get_by_id(db, payload.order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order referenced in webhook not found")

        payment = PaymentRepository.get_by_reference(db, payload.transaction_reference)
        if not payment:
            # Create payment record from webhook if not existing
            payment = PaymentRepository.create_payment(
                db=db,
                order_id=order.order_id,
                payment_method="UPI",
                amount=payload.amount,
                transaction_reference=payload.transaction_reference,
                gateway_name="WebhookGateway",
            )

        if payload.status == "SUCCESS":
            PaymentRepository.update_status(db, payment, PaymentStatus.SUCCESS)
            if order.order_status == OrderStatus.PENDING:
                OrderRepository.update_status(
                    db, order, OrderStatus.CONFIRMED, changed_by_user_id=None, notes="Confirmed via payment webhook"
                )
        elif payload.status == "FAILED":
            PaymentRepository.update_status(db, payment, PaymentStatus.FAILED, error_message="Webhook payment failed")

        redis_client.set(webhook_key, "processed", ttl_seconds=86400)
        return {"status": "success", "detail": "Webhook processed successfully"}
