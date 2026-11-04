from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Address, MenuItem, OperatingStatus
from app.repositories.address_repo import AddressRepository
from app.repositories.cart_repo import CartRepository
from app.services.cart_service import CartService
from app.schemas.address import AddressResponse
from app.schemas.checkout import CheckoutSummaryResponse, CheckoutValidateRequest


class CheckoutService:
    @staticmethod
    def validate_and_summarize(
        db: Session, customer_id: int, address_id: Optional[int] = None, coupon_code: Optional[str] = None
    ) -> CheckoutSummaryResponse:
        cart = CartService.get_cart(db, customer_id)
        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your shopping cart is empty",
            )

        validation_errors: List[str] = []

        # Check item availability
        unavailable_items = [itm.name for itm in cart.items if not itm.is_available]
        if unavailable_items:
            validation_errors.append(f"Some items in your cart are currently out of stock: {', '.join(unavailable_items)}")

        # Check address
        delivery_address_resp = None
        if address_id:
            addr = AddressRepository.get_by_id_and_customer(db, address_id, customer_id)
            if not addr:
                validation_errors.append("Selected delivery address does not exist or does not belong to your account")
            else:
                delivery_address_resp = AddressResponse.model_validate(addr)
        else:
            # Try default address
            addresses = AddressRepository.get_customer_addresses(db, customer_id)
            if addresses:
                default_addr = next((a for a in addresses if a.is_default), addresses[0])
                delivery_address_resp = AddressResponse.model_validate(default_addr)
            else:
                validation_errors.append("Please add or select a delivery address to proceed with checkout")

        return CheckoutSummaryResponse(
            subtotal_amount=cart.subtotal_amount,
            discount_amount=cart.discount_amount,
            delivery_fee=cart.delivery_fee,
            tax_amount=cart.tax_amount,
            total_amount=cart.total_amount,
            kitchen_id=cart.kitchen_id or 1,
            kitchen_name=cart.kitchen_name or "Cloud Kitchen",
            delivery_address=delivery_address_resp,
            applied_coupon_code=cart.applied_coupon_code,
            items_count=cart.items_count,
            can_place_order=len(validation_errors) == 0,
            validation_errors=validation_errors,
        )
