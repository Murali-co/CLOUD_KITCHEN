from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    order_id: int
    payment_method: str = Field(..., pattern="^(UPI|CREDIT_CARD|DEBIT_CARD|NET_BANKING|WALLET|CASH_ON_DELIVERY)$")


class PaymentVerifyRequest(BaseModel):
    order_id: int
    transaction_reference: str
    gateway_name: str = "TestGateway"
    signature: str = Field(..., description="Gateway verification signature")


class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    payment_method: str
    payment_status: str
    transaction_reference: Optional[str] = None
    gateway_name: Optional[str] = None
    amount: Decimal
    currency: str
    initiated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentWebhookPayload(BaseModel):
    event: str
    order_id: int
    transaction_reference: str
    amount: Decimal
    status: str
    signature: str
