from datetime import datetime
from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.models import Order, OrderItem, OrderStatus, OrderStatusHistory, Payment, PaymentStatus, PaymentMethod, Customer


class OrderRepository:
    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        return db.query(Order).filter(Order.order_id == order_id).first()

    @staticmethod
    def get_by_id_and_customer(db: Session, order_id: int, customer_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                joinedload(Order.order_items),
                joinedload(Order.status_history),
                joinedload(Order.delivery_address),
                joinedload(Order.payments),
            )
            .filter(Order.order_id == order_id, Order.customer_id == customer_id)
            .first()
        )

    @staticmethod
    def get_by_order_number(db: Session, order_number: str) -> Optional[Order]:
        return db.query(Order).filter(Order.order_number == order_number).first()

    @staticmethod
    def get_customer_orders(
        db: Session, customer_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Order], int]:
        query = (
            db.query(Order)
            .options(joinedload(Order.order_items))
            .filter(Order.customer_id == customer_id)
            .order_by(Order.placed_at.desc())
        )
        total = query.count()
        orders = query.offset(skip).limit(limit).all()
        return orders, total

    @staticmethod
    def create_order(
        db: Session,
        order_number: str,
        customer_id: int,
        kitchen_id: int,
        delivery_address_id: int,
        subtotal: Decimal,
        discount: Decimal,
        delivery_fee: Decimal,
        tax: Decimal,
        total: Decimal,
        applied_coupon_id: Optional[int],
        special_instructions: Optional[str],
        items: List[dict],
        payment_method: str,
    ) -> Order:
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            kitchen_id=kitchen_id,
            delivery_address_id=delivery_address_id,
            order_status=OrderStatus.PENDING,
            subtotal_amount=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            delivery_fee=delivery_fee,
            total_amount=total,
            applied_coupon_id=applied_coupon_id,
            special_instructions=special_instructions,
        )
        db.add(order)
        db.flush()

        # Insert items snapshots
        for itm in items:
            order_item = OrderItem(
                order_id=order.order_id,
                menu_item_id=itm["menu_item_id"],
                item_name_snapshot=itm["name"],
                unit_price_snapshot=itm["unit_price"],
                quantity=itm["quantity"],
                subtotal_price=itm["subtotal_price"],
                customization_notes=itm.get("customization_notes"),
            )
            db.add(order_item)

        # Initial status history
        history = OrderStatusHistory(
            order_id=order.order_id,
            previous_status=None,
            new_status=OrderStatus.PENDING,
            changed_by_user_id=customer_id,
            notes="Order placed by customer",
        )
        db.add(history)

        # Initial payment record
        pay_enum = PaymentMethod[payment_method] if payment_method in PaymentMethod.__members__ else PaymentMethod.UPI
        payment = Payment(
            order_id=order.order_id,
            payment_method=pay_enum,
            payment_status=PaymentStatus.PENDING,
            amount=total,
            currency="INR",
            gateway_name="TestPaymentGateway",
        )
        db.add(payment)

        db.flush()
        return order

    @staticmethod
    def update_status(
        db: Session, order: Order, new_status: OrderStatus, changed_by_user_id: Optional[int], notes: Optional[str] = None
    ) -> Order:
        prev = order.order_status
        order.order_status = new_status
        history = OrderStatusHistory(
            order_id=order.order_id,
            previous_status=prev,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
            notes=notes,
        )
        db.add(history)
        db.flush()
        return order

    @staticmethod
    def get_kitchen_orders(
        db: Session,
        kitchen_id: int,
        status: Optional[OrderStatus] = None,
        date_filter: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Order], int]:
        query = (
            db.query(Order)
            .options(
                joinedload(Order.customer).joinedload(Customer.user),
                joinedload(Order.order_items),
                joinedload(Order.payments),
            )
            .filter(Order.kitchen_id == kitchen_id)
        )
        if status:
            query = query.filter(Order.order_status == status)
        if date_filter:
            start_of_day = datetime(date_filter.year, date_filter.month, date_filter.day, 0, 0, 0)
            end_of_day = datetime(date_filter.year, date_filter.month, date_filter.day, 23, 59, 59)
            query = query.filter(Order.placed_at >= start_of_day, Order.placed_at <= end_of_day)
        if search:
            search_clean = search.strip()
            query = query.filter(
                (Order.order_number.ilike(f"%{search_clean}%"))
                | (Order.order_id == int(search_clean) if search_clean.isdigit() else False)
            )

        total = query.count()
        orders = query.order_by(Order.placed_at.desc()).offset(skip).limit(limit).all()
        return orders, total

    @staticmethod
    def get_kitchen_order_by_id(db: Session, order_id: int, kitchen_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                joinedload(Order.customer).joinedload(Customer.user),
                joinedload(Order.order_items),
                joinedload(Order.status_history).joinedload(OrderStatusHistory.changed_by_user),
                joinedload(Order.delivery_address),
                joinedload(Order.payments),
            )
            .filter(Order.order_id == order_id, Order.kitchen_id == kitchen_id)
            .first()
        )

    @staticmethod
    def get_kitchen_dashboard_stats(db: Session, kitchen_id: int) -> dict:
        now = datetime.utcnow()
        start_of_today = datetime(now.year, now.month, now.day, 0, 0, 0)

        total_today = (
            db.query(func.count(Order.order_id))
            .filter(Order.kitchen_id == kitchen_id, Order.placed_at >= start_of_today)
            .scalar()
            or 0
        )

        new_orders = (
            db.query(func.count(Order.order_id))
            .filter(Order.kitchen_id == kitchen_id, Order.order_status == OrderStatus.PENDING)
            .scalar()
            or 0
        )

        confirmed = (
            db.query(func.count(Order.order_id))
            .filter(Order.kitchen_id == kitchen_id, Order.order_status == OrderStatus.CONFIRMED)
            .scalar()
            or 0
        )

        preparing = (
            db.query(func.count(Order.order_id))
            .filter(Order.kitchen_id == kitchen_id, Order.order_status == OrderStatus.PREPARING)
            .scalar()
            or 0
        )

        ready = (
            db.query(func.count(Order.order_id))
            .filter(Order.kitchen_id == kitchen_id, Order.order_status == OrderStatus.READY_FOR_PICKUP)
            .scalar()
            or 0
        )

        completed_today = (
            db.query(func.count(Order.order_id))
            .filter(
                Order.kitchen_id == kitchen_id,
                Order.order_status == OrderStatus.DELIVERED,
                Order.placed_at >= start_of_today,
            )
            .scalar()
            or 0
        )

        cancelled_today = (
            db.query(func.count(Order.order_id))
            .filter(
                Order.kitchen_id == kitchen_id,
                Order.order_status == OrderStatus.CANCELLED,
                Order.placed_at >= start_of_today,
            )
            .scalar()
            or 0
        )

        recent_orders = (
            db.query(Order)
            .options(joinedload(Order.customer).joinedload(Customer.user))
            .filter(Order.kitchen_id == kitchen_id)
            .order_by(Order.placed_at.desc())
            .limit(10)
            .all()
        )

        return {
            "total_today": total_today,
            "new_orders": new_orders,
            "confirmed": confirmed,
            "preparing": preparing,
            "ready": ready,
            "completed_today": completed_today,
            "cancelled_today": cancelled_today,
            "recent_orders": recent_orders,
        }

    @staticmethod
    def get_kitchen_queue(db: Session, kitchen_id: int) -> List[Order]:
        active_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY_FOR_PICKUP,
        ]
        return (
            db.query(Order)
            .options(
                joinedload(Order.customer).joinedload(Customer.user),
                joinedload(Order.order_items),
            )
            .filter(Order.kitchen_id == kitchen_id, Order.order_status.in_(active_statuses))
            .order_by(Order.placed_at.asc())
            .all()
        )

