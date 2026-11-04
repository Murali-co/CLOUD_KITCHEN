from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_customer
from app.db.database import get_db
from app.models import User
from app.schemas.checkout import CheckoutSummaryResponse, CheckoutValidateRequest
from app.schemas.common import StandardResponse
from app.services.checkout_service import CheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.get("/summary", response_model=StandardResponse[CheckoutSummaryResponse])
def get_checkout_summary(
    address_id: Optional[int] = Query(None, description="Selected delivery address ID"),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Calculates server-authoritative checkout summary, item availability, and address check."""
    summary = CheckoutService.validate_and_summarize(db, current_user.user_id, address_id=address_id)
    return StandardResponse(success=True, data=summary)


@router.post("/validate", response_model=StandardResponse[CheckoutSummaryResponse])
def validate_checkout(
    data: CheckoutValidateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Validates entire checkout payload before initiating order creation."""
    summary = CheckoutService.validate_and_summarize(
        db, current_user.user_id, address_id=data.delivery_address_id, coupon_code=data.coupon_code
    )
    return StandardResponse(success=True, data=summary)
