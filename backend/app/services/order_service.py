import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.redis import redis_client
from app.models import (
    Address,
    Coupon,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.repositories.address_repo import AddressRepository
from app.repositories.coupon_repo import CouponRepository
from app.repositories.order_repo import OrderRepository
from app.services.cart_service import CartService
from app.schemas.address import AddressResponse
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.order import (
    OrderCancelRequest,
    OrderCreateRequest,
    OrderDetailResponse,
    OrderItemResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
)


class OrderService:
    @staticmethod
    def place_order(db: Session, customer_id: int, data: OrderCreateRequest) -> OrderDetailResponse:
        # Idempotency Protection
        idempotency_key = f"idempotency:order:{data.idempotency_key}"
        existing_order_id = redis_client.get(idempotency_key)
        if existing_order_id:
            # Duplicate submission detected, return existing order
            existing_order = OrderRepository.get_by_id_and_customer(db, int(existing_order_id), customer_id)
            if existing_order:
                return OrderService.get_order_detail(db, existing_order.order_id, customer_id)

        # 1. Fetch current cart
        cart = CartService.get_cart(db, customer_id)
        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot place an order with an empty shopping cart",
            )

        # 2. Validate items availability
        unavailable = [i.name for i in cart.items if not i.is_available]
        if unavailable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following items are unavailable: {', '.join(unavailable)}",
            )

        # 3. Validate delivery address ownership
        address = AddressRepository.get_by_id_and_customer(db, data.delivery_address_id, customer_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The chosen delivery address does not exist or does not belong to you",
            )

        kitchen_id = cart.kitchen_id
        if not kitchen_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to determine preparing kitchen for cart items",
            )

        # 4. Generate unique order number
        today_str = datetime.utcnow().strftime("%Y%m%d")
        rand_suffix = str(uuid.uuid4().hex[:6]).upper()
        order_number = f"ORD-{today_str}-{rand_suffix}"

        # 5. Coupon validation
        coupon_id = None
        coupon = None
        if cart.applied_coupon_code:
            coupon = CouponRepository.get_by_code(db, cart.applied_coupon_code)
            if coupon and coupon.is_active:
                coupon_id = coupon.coupon_id

        # 6. Execute atomic database transaction
        try:
            items_payload = [
                {
                    "menu_item_id": itm.menu_item_id,
                    "name": itm.name,
                    "unit_price": itm.unit_price,
                    "quantity": itm.quantity,
                    "subtotal_price": itm.subtotal_price,
                    "customization_notes": itm.customization_notes,
                }
                for itm in cart.items
            ]

            order = OrderRepository.create_order(
                db=db,
                order_number=order_number,
                customer_id=customer_id,
                kitchen_id=kitchen_id,
                delivery_address_id=address.address_id,
                subtotal=cart.subtotal_amount,
                discount=cart.discount_amount,
                delivery_fee=cart.delivery_fee,
                tax=cart.tax_amount,
                total=cart.total_amount,
                applied_coupon_id=coupon_id,
                special_instructions=data.special_instructions,
                items=items_payload,
                payment_method=data.payment_method,
            )

            if coupon and cart.discount_amount > Decimal("0.00"):
                CouponRepository.record_usage(db, coupon, customer_id, order.order_id, cart.discount_amount)

            db.commit()
            db.refresh(order)

            # Store in idempotency cache (24 hours TTL)
            redis_client.set(idempotency_key, str(order.order_id), ttl_seconds=86400)

            # Clear Redis shopping cart on successful commit
            CartService.clear_cart(customer_id)

            # Initialize live status tracking in Redis (2 hours TTL)
            try:
                redis_client.set_json(
                    f"order:{order.order_id}:status",
                    {
                        "order_id": order.order_id,
                        "order_number": order.order_number,
                        "order_status": order.order_status.value,
                        "placed_at": str(order.placed_at),
                    },
                    ttl_seconds=7200,
                )
                redis_client.delete(f"kitchen:{kitchen_id}:order_queue")
                redis_client.delete("admin:dashboard:metrics")
            except Exception:
                pass

            return OrderService.get_order_detail(db, order.order_id, customer_id)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to place order: {str(e)}",
            )

    @staticmethod
    def get_order_detail(db: Session, order_id: int, customer_id: int) -> OrderDetailResponse:
        order = OrderRepository.get_by_id_and_customer(db, order_id, customer_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or unauthorized access",
            )

        items_resp = [
            OrderItemResponse(
                order_item_id=i.order_item_id,
                menu_item_id=i.menu_item_id,
                item_name_snapshot=i.item_name_snapshot,
                unit_price_snapshot=i.unit_price_snapshot,
                quantity=i.quantity,
                subtotal_price=i.subtotal_price,
                customization_notes=i.customization_notes,
            )
            for i in order.order_items
        ]

        history_resp = [
            OrderStatusHistoryResponse(
                history_id=h.history_id,
                previous_status=h.previous_status.value if h.previous_status else None,
                new_status=h.new_status.value if hasattr(h.new_status, "value") else str(h.new_status),
                notes=h.notes,
                created_at=h.created_at,
            )
            for h in order.status_history
        ]

        # Latest payment info
        latest_payment = order.payments[-1] if order.payments else None

        return OrderDetailResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            kitchen_id=order.kitchen_id,
            order_status=order.order_status.value if hasattr(order.order_status, "value") else str(order.order_status),
            subtotal_amount=order.subtotal_amount,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            delivery_fee=order.delivery_fee,
            total_amount=order.total_amount,
            items_count=sum(i.quantity for i in items_resp),
            placed_at=order.placed_at,
            special_instructions=order.special_instructions,
            estimated_delivery_time=order.estimated_delivery_time,
            delivery_address=AddressResponse.model_validate(order.delivery_address) if order.delivery_address else None,
            items=items_resp,
            status_history=history_resp,
            payment_status=latest_payment.payment_status.value if latest_payment else None,
            payment_method=latest_payment.payment_method.value if latest_payment else None,
        )

    @staticmethod
    def list_customer_orders(
        db: Session, customer_id: int, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[OrderResponse]:
        skip = (page - 1) * page_size
        orders, total = OrderRepository.get_customer_orders(db, customer_id, skip=skip, limit=page_size)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        items = []
        for o in orders:
            items.append(
                OrderResponse(
                    order_id=o.order_id,
                    order_number=o.order_number,
                    kitchen_id=o.kitchen_id,
                    order_status=o.order_status.value if hasattr(o.order_status, "value") else str(o.order_status),
                    subtotal_amount=o.subtotal_amount,
                    discount_amount=o.discount_amount,
                    tax_amount=o.tax_amount,
                    delivery_fee=o.delivery_fee,
                    total_amount=o.total_amount,
                    items_count=sum(item.quantity for item in o.order_items),
                    placed_at=o.placed_at,
                )
            )

        return PaginatedResponse(
            items=items,
            meta=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        )

    @staticmethod
    def cancel_order(db: Session, order_id: int, customer_id: int, reason: Optional[str] = None) -> OrderDetailResponse:
        order = OrderRepository.get_by_id_and_customer(db, order_id, customer_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or unauthorized access",
            )

        # Business rule for customer cancellations: allowed only before preparation begins
        allowed_cancellation_states = [OrderStatus.PENDING, OrderStatus.CONFIRMED]
        if order.order_status not in allowed_cancellation_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be cancelled in status '{order.order_status.value}'. Kitchen preparation has already started.",
            )

        notes = f"Cancelled by customer: {reason.strip() if reason else 'No reason provided'}"
        OrderRepository.update_status(db, order, OrderStatus.CANCELLED, customer_id, notes=notes)

        # Invalidate status and tracking caches
        try:
            redis_client.delete(f"order:{order_id}:status")
            redis_client.delete(f"order:tracking:{order_id}")
            redis_client.delete(f"kitchen:{order.kitchen_id}:order_queue")
            redis_client.delete("admin:dashboard:metrics")
        except Exception:
            pass

        return OrderService.get_order_detail(db, order_id, customer_id)
