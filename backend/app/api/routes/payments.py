from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_customer
from app.db.database import get_db
from app.models import User
from app.repositories.payment_repo import PaymentRepository
from app.schemas.common import StandardResponse
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    PaymentVerifyRequest,
    PaymentWebhookPayload,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create", response_model=StandardResponse[Dict[str, Any]])
def create_payment_order(
    data: PaymentCreateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Initializes a payment transaction with the payment provider / test gateway."""
    resp = PaymentService.create_payment_order(db, current_user.user_id, data)
    return StandardResponse(success=True, data=resp)


@router.post("/verify", response_model=StandardResponse[PaymentResponse])
def verify_payment(
    data: PaymentVerifyRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Cryptographically verifies payment signature and advances order to CONFIRMED."""
    payment_resp = PaymentService.verify_payment(db, current_user.user_id, data)
    return StandardResponse(
        success=True,
        message="Payment verified successfully! Order is now confirmed.",
        data=payment_resp,
    )


@router.post("/webhook", response_model=StandardResponse[dict])
def payment_webhook(
    payload: PaymentWebhookPayload,
    db: Session = Depends(get_db),
):
    """Secure webhook handler for asynchronous gateway event notifications."""
    resp = PaymentService.handle_webhook(db, payload)
    return StandardResponse(success=True, data=resp)


@router.get("/{payment_id}", response_model=StandardResponse[PaymentResponse])
def get_payment_status(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves status of a specific payment transaction."""
    payment = PaymentRepository.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found",
        )
    return StandardResponse(success=True, data=PaymentResponse.model_validate(payment))
