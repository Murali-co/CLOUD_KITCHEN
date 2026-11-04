from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import require_customer
from app.db.database import get_db
from app.models import User
from app.schemas.address import AddressCreateRequest, AddressResponse, AddressUpdateRequest
from app.schemas.common import StandardResponse
from app.schemas.user import CustomerProfileResponse, CustomerProfileUpdateRequest
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customer", tags=["Customer Operations"])


@router.get("/profile", response_model=StandardResponse[CustomerProfileResponse])
def get_customer_profile(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Retrieves customer-specific profile including loyalty rewards and preferences."""
    profile = CustomerService.get_profile(db, current_user)
    return StandardResponse(success=True, data=profile)


@router.put("/profile", response_model=StandardResponse[CustomerProfileResponse])
def update_customer_profile(
    data: CustomerProfileUpdateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Updates customer names, telephone, and dietary preference."""
    updated = CustomerService.update_profile(db, current_user, data)
    return StandardResponse(success=True, message="Profile updated successfully", data=updated)


@router.get("/addresses", response_model=StandardResponse[List[AddressResponse]])
def list_addresses(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Lists all saved delivery addresses for the authenticated customer."""
    addresses = CustomerService.list_addresses(db, current_user.user_id)
    return StandardResponse(success=True, data=addresses)


@router.post("/addresses", response_model=StandardResponse[AddressResponse], status_code=status.HTTP_201_CREATED)
def add_address(
    data: AddressCreateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Saves a new delivery address for the customer."""
    addr = CustomerService.add_address(db, current_user.user_id, data)
    return StandardResponse(success=True, message="Delivery address saved", data=addr)


@router.put("/addresses/{address_id}", response_model=StandardResponse[AddressResponse])
def update_address(
    address_id: int,
    data: AddressUpdateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Updates an existing delivery address owned by the customer."""
    updated = CustomerService.update_address(db, current_user.user_id, address_id, data)
    return StandardResponse(success=True, message="Address updated", data=updated)


@router.delete("/addresses/{address_id}", response_model=StandardResponse[dict])
def delete_address(
    address_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Deletes a delivery address owned by the customer."""
    CustomerService.delete_address(db, current_user.user_id, address_id)
    return StandardResponse(success=True, message="Address deleted", data={"deleted": True})
