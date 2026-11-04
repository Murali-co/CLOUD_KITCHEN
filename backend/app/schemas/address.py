from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class AddressCreateRequest(BaseModel):
    address_label: str = Field("Home", max_length=50)
    recipient_name: str = Field(..., min_length=2, max_length=150)
    recipient_phone: str = Field(..., min_length=8, max_length=20)
    address_line1: str = Field(..., min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    landmark: Optional[str] = Field(None, max_length=150)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: bool = False


class AddressUpdateRequest(BaseModel):
    address_label: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    address_id: int
    customer_id: int
    address_label: str
    recipient_name: str
    recipient_phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    postal_code: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    is_default: bool

    class Config:
        from_attributes = True
