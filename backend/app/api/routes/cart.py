from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_customer
from app.db.database import get_db
from app.models import User
from app.schemas.cart import ApplyCouponRequest, CartItemAddRequest, CartItemUpdateRequest, CartResponse
from app.schemas.common import StandardResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.get("", response_model=StandardResponse[CartResponse])
def get_cart(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Retrieves current customer cart recalculated with authoritative MySQL prices."""
    cart = CartService.get_cart(db, current_user.user_id)
    return StandardResponse(success=True, data=cart)


@router.post("/items", response_model=StandardResponse[CartResponse])
def add_to_cart(
    data: CartItemAddRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Adds a dish to cart, enforcing single-kitchen and availability rules."""
    cart = CartService.add_item(db, current_user.user_id, data)
    return StandardResponse(success=True, message="Item added to cart", data=cart)


@router.put("/items/{item_id}", response_model=StandardResponse[CartResponse])
def update_cart_item(
    item_id: int,
    data: CartItemUpdateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Updates quantity or customization instructions for a cart item."""
    cart = CartService.update_item_quantity(db, current_user.user_id, item_id, data.quantity, data.customization_notes)
    return StandardResponse(success=True, message="Cart updated", data=cart)


@router.delete("/items/{item_id}", response_model=StandardResponse[CartResponse])
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Removes an item from the cart."""
    cart = CartService.remove_item(db, current_user.user_id, item_id)
    return StandardResponse(success=True, message="Item removed from cart", data=cart)


@router.delete("", response_model=StandardResponse[dict])
def clear_cart(
    current_user: User = Depends(require_customer),
):
    """Flushes all items and applied coupon from the current customer cart."""
    CartService.clear_cart(current_user.user_id)
    return StandardResponse(success=True, message="Cart cleared", data={"cleared": True})


@router.post("/apply-coupon", response_model=StandardResponse[CartResponse])
def apply_coupon(
    data: ApplyCouponRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Validates and applies a promotional voucher to the cart."""
    cart = CartService.apply_coupon(db, current_user.user_id, data.coupon_code)
    return StandardResponse(success=True, message=f"Coupon '{data.coupon_code}' applied successfully!", data=cart)


@router.delete("/remove-coupon", response_model=StandardResponse[CartResponse])
def remove_coupon(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Removes active promotional discount from the cart."""
    cart = CartService.remove_coupon(db, current_user.user_id)
    return StandardResponse(success=True, message="Coupon removed", data=cart)
