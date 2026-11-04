from datetime import datetime, date, time
from typing import List, Optional, Tuple
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.fulfillment import Delivery, DeliveryStatus
from app.models.kitchen import Kitchen
from app.models.order import Order, OrderStatus, OrderStatusHistory
from app.models.user import Customer, DeliveryPerson, DeliveryPersonStatus, User


class DeliveryRepository:
    @staticmethod
    def get_profile(db: Session, delivery_person_id: int) -> Optional[DeliveryPerson]:
        return (
            db.query(DeliveryPerson)
            .options(joinedload(DeliveryPerson.user))
            .filter(DeliveryPerson.delivery_person_id == delivery_person_id)
            .first()
        )

    @staticmethod
    def update_availability(
        db: Session, delivery_person_id: int, status: DeliveryPersonStatus
    ) -> Optional[DeliveryPerson]:
        driver = (
            db.query(DeliveryPerson)
            .options(joinedload(DeliveryPerson.user))
            .filter(DeliveryPerson.delivery_person_id == delivery_person_id)
            .first()
        )
        if driver:
            driver.current_status = status
            db.flush()
        return driver

    @staticmethod
    def get_dashboard_stats(db: Session, delivery_person_id: int) -> dict:
        driver = db.query(DeliveryPerson).filter(DeliveryPerson.delivery_person_id == delivery_person_id).first()
        driver_status = driver.current_status if driver else DeliveryPersonStatus.OFF_DUTY

        active_deliveries = (
            db.query(Delivery)
            .filter(
                Delivery.delivery_person_id == delivery_person_id,
                Delivery.delivery_status.in_([DeliveryStatus.ASSIGNED, DeliveryStatus.PICKED_UP, DeliveryStatus.OUT_FOR_DELIVERY]),
            )
            .all()
        )

        assigned_count = len(active_deliveries)
        pending_pickup = sum(1 for d in active_deliveries if d.delivery_status == DeliveryStatus.ASSIGNED)
        picked_up = sum(1 for d in active_deliveries if d.delivery_status == DeliveryStatus.PICKED_UP)
        out_for_delivery = sum(1 for d in active_deliveries if d.delivery_status == DeliveryStatus.OUT_FOR_DELIVERY)

        today_start = datetime.combine(date.today(), time.min)
        delivered_today = (
            db.query(Delivery)
            .filter(
                Delivery.delivery_person_id == delivery_person_id,
                Delivery.delivery_status == DeliveryStatus.DELIVERED,
                Delivery.delivered_at >= today_start,
            )
            .count()
        )

        return {
            "assigned_deliveries": assigned_count,
            "pending_pickup": pending_pickup,
            "picked_up_orders": picked_up,
            "out_for_delivery_orders": out_for_delivery,
            "delivered_orders_today": delivered_today,
            "current_status": driver_status,
        }

    @staticmethod
    def get_assignments(
        db: Session,
        delivery_person_id: int,
        delivery_status: Optional[DeliveryStatus] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Delivery], int]:
        query = (
            db.query(Delivery)
            .options(
                joinedload(Delivery.order).joinedload(Order.customer).joinedload(Customer.user),
                joinedload(Delivery.order).joinedload(Order.kitchen),
                joinedload(Delivery.order).joinedload(Order.delivery_address),
                joinedload(Delivery.order).joinedload(Order.payments),
            )
            .filter(Delivery.delivery_person_id == delivery_person_id)
        )

        if delivery_status:
            query = query.filter(Delivery.delivery_status == delivery_status)
        elif active_only:
            query = query.filter(
                Delivery.delivery_status.in_([
                    DeliveryStatus.ASSIGNED,
                    DeliveryStatus.PICKED_UP,
                    DeliveryStatus.OUT_FOR_DELIVERY,
                ])
            )

        total = query.count()
        deliveries = query.order_by(desc(Delivery.created_at)).offset(skip).limit(limit).all()
        return deliveries, total

    @staticmethod
    def get_delivery_by_id(db: Session, delivery_id: int) -> Optional[Delivery]:
        return (
            db.query(Delivery)
            .options(
                joinedload(Delivery.order).joinedload(Order.customer).joinedload(Customer.user),
                joinedload(Delivery.order).joinedload(Order.kitchen),
                joinedload(Delivery.order).joinedload(Order.delivery_address),
                joinedload(Delivery.order).joinedload(Order.order_items),
                joinedload(Delivery.order).joinedload(Order.payments),
                joinedload(Delivery.order).joinedload(Order.status_history),
                joinedload(Delivery.delivery_person).joinedload(DeliveryPerson.user),
            )
            .filter(Delivery.delivery_id == delivery_id)
            .first()
        )

    @staticmethod
    def get_delivery_by_order_id(db: Session, order_id: int) -> Optional[Delivery]:
        return (
            db.query(Delivery)
            .options(
                joinedload(Delivery.delivery_person).joinedload(DeliveryPerson.user),
                joinedload(Delivery.order),
            )
            .filter(Delivery.order_id == order_id)
            .first()
        )

    @staticmethod
    def get_available_personnel(db: Session) -> List[DeliveryPerson]:
        return (
            db.query(DeliveryPerson)
            .join(DeliveryPerson.user)
            .filter(
                DeliveryPerson.current_status == DeliveryPersonStatus.AVAILABLE,
                User.is_active == True,
            )
            .options(joinedload(DeliveryPerson.user))
            .all()
        )

    @staticmethod
    def create_or_assign_delivery(
        db: Session,
        order_id: int,
        delivery_person_id: int,
        delivery_otp: Optional[str] = None,
    ) -> Delivery:
        existing = db.query(Delivery).filter(Delivery.order_id == order_id).first()
        if existing:
            existing.delivery_person_id = delivery_person_id
            existing.delivery_status = DeliveryStatus.ASSIGNED
            existing.assigned_at = datetime.utcnow()
            existing.delivery_otp = delivery_otp or existing.delivery_otp
            db.flush()
            return existing

        delivery = Delivery(
            order_id=order_id,
            delivery_person_id=delivery_person_id,
            delivery_status=DeliveryStatus.ASSIGNED,
            delivery_otp=delivery_otp,
            assigned_at=datetime.utcnow(),
        )
        db.add(delivery)
        db.flush()
        return delivery
