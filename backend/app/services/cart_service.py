from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import MenuItem, Coupon, OperatingStatus
from app.repositories.cart_repo import CartRepository
from app.repositories.coupon_repo import CouponRepository
from app.schemas.cart import CartItemAddRequest, CartItemResponse, CartResponse


class CartService:
    @classmethod
    def get_cart(cls, db: Session, customer_id: int) -> CartResponse:
        raw_items = CartRepository.get_cart_raw(customer_id)
        if not raw_items:
            return CartResponse()

        menu_item_ids = [int(k) for k in raw_items.keys()]
        dishes = db.query(MenuItem).filter(MenuItem.menu_item_id.in_(menu_item_ids)).all()
        dish_map = {d.menu_item_id: d for d in dishes}

        items_resp: List[CartItemResponse] = []
        subtotal = Decimal("0.00")
        kitchen_id = None
        kitchen_name = None

        for item_id_str, data in raw_items.items():
            item_id = int(item_id_str)
            dish = dish_map.get(item_id)
            if not dish:
                continue

            quantity = data.get("quantity", 1)
            line_total = Decimal(str(dish.base_price)) * Decimal(str(quantity))
            subtotal += line_total

            if kitchen_id is None and dish.kitchen:
                kitchen_id = dish.kitchen_id
                kitchen_name = dish.kitchen.name

            items_resp.append(
                CartItemResponse(
                    menu_item_id=dish.menu_item_id,
                    name=dish.name,
                    unit_price=dish.base_price,
                    quantity=quantity,
                    subtotal_price=line_total,
                    is_available=dish.is_available,
                    customization_notes=data.get("customization_notes"),
                )
            )

        # Delivery fee logic: standard Rs 40; free delivery on orders >= Rs 500
        delivery_fee = Decimal("0.00") if subtotal >= Decimal("500.00") or subtotal == Decimal("0.00") else Decimal("40.00")

        # Tax calculation (5% standard GST on food)
        tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))

        # Coupon calculation
        discount = Decimal("0.00")
        applied_coupon_code = CartRepository.get_coupon(customer_id)
        if applied_coupon_code and subtotal > Decimal("0.00"):
            coupon = CouponRepository.get_by_code(db, applied_coupon_code)
            if coupon and coupon.is_active and coupon.valid_from <= datetime.utcnow() <= coupon.valid_to:
                if subtotal >= coupon.min_order_value:
                    if coupon.discount_type.value == "PERCENTAGE":
                        calc_discount = (subtotal * (coupon.discount_value / Decimal("100.00"))).quantize(Decimal("0.01"))
                        if coupon.max_discount_amount:
                            calc_discount = min(calc_discount, coupon.max_discount_amount)
                        discount = calc_discount
                    else:  # FIXED_AMOUNT
                        discount = min(coupon.discount_value, subtotal)
                        if coupon.code == "FREESHIP":
                            delivery_fee = Decimal("0.00")
                else:
                    # Minimum order value not met, ignore coupon for now
                    pass
            else:
                applied_coupon_code = None
                CartRepository.remove_coupon(customer_id)

        total = max(Decimal("0.00"), subtotal - discount + delivery_fee + tax).quantize(Decimal("0.01"))

        return CartResponse(
            items=items_resp,
            subtotal_amount=subtotal.quantize(Decimal("0.01")),
            discount_amount=discount.quantize(Decimal("0.01")),
            delivery_fee=delivery_fee.quantize(Decimal("0.01")),
            tax_amount=tax.quantize(Decimal("0.01")),
            total_amount=total,
            kitchen_id=kitchen_id,
            kitchen_name=kitchen_name,
            applied_coupon_code=applied_coupon_code,
            items_count=sum(i.quantity for i in items_resp),
        )

    @classmethod
    def add_item(cls, db: Session, customer_id: int, data: CartItemAddRequest) -> CartResponse:
        dish = db.query(MenuItem).filter(MenuItem.menu_item_id == data.menu_item_id).first()
        if not dish:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item with ID {data.menu_item_id} not found",
            )

        if not dish.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{dish.name}' is currently unavailable or out of stock",
            )

        # Check kitchen active status
        if dish.kitchen.operating_status != OperatingStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kitchen '{dish.kitchen.name}' is currently not accepting orders",
            )

        # Check single-kitchen rule
        raw_items = CartRepository.get_cart_raw(customer_id)
        if raw_items:
            existing_ids = [int(k) for k in raw_items.keys()]
            existing_kitchens = db.query(MenuItem.kitchen_id).filter(MenuItem.menu_item_id.in_(existing_ids)).distinct().all()
            if existing_kitchens:
                current_kitchen_id = existing_kitchens[0][0]
                if current_kitchen_id != dish.kitchen_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Your cart already contains items from a different kitchen. Please clear your cart before ordering from another branch.",
                    )

        # Check if already in cart to increment quantity
        existing_qty = 0
        if str(data.menu_item_id) in raw_items:
            existing_qty = raw_items[str(data.menu_item_id)].get("quantity", 0)

        new_qty = existing_qty + data.quantity
        CartRepository.set_item(customer_id, data.menu_item_id, new_qty, data.customization_notes)
        return cls.get_cart(db, customer_id)

    @classmethod
    def update_item_quantity(cls, db: Session, customer_id: int, item_id: int, quantity: int, notes: Optional[str] = None) -> CartResponse:
        raw_items = CartRepository.get_cart_raw(customer_id)
        if str(item_id) not in raw_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in your cart",
            )

        if quantity <= 0:
            CartRepository.remove_item(customer_id, item_id)
        else:
            CartRepository.set_item(customer_id, item_id, quantity, notes)

        return cls.get_cart(db, customer_id)

    @classmethod
    def remove_item(cls, db: Session, customer_id: int, item_id: int) -> CartResponse:
        CartRepository.remove_item(customer_id, item_id)
        return cls.get_cart(db, customer_id)

    @classmethod
    def clear_cart(cls, customer_id: int) -> bool:
        return CartRepository.clear_cart(customer_id)

    @classmethod
    def apply_coupon(cls, db: Session, customer_id: int, code: str) -> CartResponse:
        coupon = CouponRepository.get_by_code(db, code)
        if not coupon or not coupon.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired coupon code",
            )

        now = datetime.utcnow()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This promotional coupon is not active at this time",
            )

        if coupon.current_usage_count >= coupon.total_usage_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This coupon has reached its total campaign redemption limit",
            )

        # Check per-customer usage count
        user_usage = CouponRepository.get_customer_usage_count(db, coupon.coupon_id, customer_id)
        if user_usage >= coupon.usage_limit_per_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already redeemed coupon '{coupon.code}' the maximum allowed number of times ({coupon.usage_limit_per_user})",
            )

        # Re-evaluate with current cart
        cart = cls.get_cart(db, customer_id)
        if cart.subtotal_amount < coupon.min_order_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum cart order value of Rs {coupon.min_order_value} required for coupon '{coupon.code}'",
            )

        CartRepository.set_coupon(customer_id, coupon.code)
        return cls.get_cart(db, customer_id)

    @classmethod
    def remove_coupon(cls, db: Session, customer_id: int) -> CartResponse:
        CartRepository.remove_coupon(customer_id)
        return cls.get_cart(db, customer_id)
