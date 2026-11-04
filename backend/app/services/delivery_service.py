import random
from datetime import datetime, date, time
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.auth import DeliveryContext
from app.db.redis import redis_client
from app.models.fulfillment import Delivery, DeliveryStatus
from app.models.order import Order, OrderStatus, OrderStatusHistory
from app.models.user import DeliveryPerson, DeliveryPersonStatus, User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.repositories.delivery_repo import DeliveryRepository
from app.schemas.delivery import (
    AvailablePersonnelOut,
    DeliveryAssignmentDetail,
    DeliveryAssignmentItem,
    DeliveryDashboardStats,
    DeliveryItemSummary,
    DeliveryPersonProfileOut,
    DeliveryStatusUpdate,
    OrderTrackingOut,
    TrackingStatusPoint,
)


class DeliveryService:
    @staticmethod
    def get_profile(db: Session, driver_ctx: DeliveryContext) -> DeliveryPersonProfileOut:
        driver = driver_ctx.delivery_person
        user = driver_ctx.user
        return DeliveryPersonProfileOut(
            delivery_person_id=driver.delivery_person_id,
            user_id=user.user_id,
            full_name=f"{user.first_name} {user.last_name}",
            email=user.email,
            phone=user.phone_number,
            vehicle_type=driver.vehicle_type,
            vehicle_number=driver.vehicle_number,
            driving_license_number=driver.driving_license_number,
            current_status=driver.current_status,
            rating=driver.rating,
            created_at=driver.created_at,
        )

    @staticmethod
    def update_availability(
        db: Session, driver_ctx: DeliveryContext, new_status: DeliveryPersonStatus
    ) -> DeliveryPersonProfileOut:
        # Drivers cannot set themselves to AVAILABLE if they currently have an ongoing delivery
        if new_status == DeliveryPersonStatus.AVAILABLE:
            active_del = (
                db.query(Delivery)
                .filter(
                    Delivery.delivery_person_id == driver_ctx.delivery_person_id,
                    Delivery.delivery_status.in_([DeliveryStatus.PICKED_UP, DeliveryStatus.OUT_FOR_DELIVERY]),
                )
                .first()
            )
            if active_del:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot toggle to AVAILABLE while currently engaged in an active delivery task",
                )

        updated_driver = DeliveryRepository.update_availability(db, driver_ctx.delivery_person_id, new_status)
        db.commit()
        db.refresh(updated_driver)
        return DeliveryService.get_profile(db, driver_ctx)

    @staticmethod
    def get_dashboard_stats(db: Session, driver_ctx: DeliveryContext) -> DeliveryDashboardStats:
        stats = DeliveryRepository.get_dashboard_stats(db, driver_ctx.delivery_person_id)
        return DeliveryDashboardStats(**stats)

    @staticmethod
    def list_assignments(
        db: Session,
        driver_ctx: DeliveryContext,
        delivery_status: Optional[DeliveryStatus] = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[DeliveryAssignmentItem], int]:
        deliveries, total = DeliveryRepository.get_assignments(
            db=db,
            delivery_person_id=driver_ctx.delivery_person_id,
            delivery_status=delivery_status,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

        items = []
        for d in deliveries:
            order = d.order
            kitchen = order.kitchen
            cust_user = order.customer.user if (order.customer and hasattr(order.customer, "user")) else None
            cust_name = f"{cust_user.first_name} {cust_user.last_name}" if cust_user else "Customer"
            cust_phone = cust_user.phone_number if cust_user else None

            addr = "Takeaway / Dine-in"
            if order.delivery_address:
                addr = f"{order.delivery_address.address_line1}, {order.delivery_address.city} - {order.delivery_address.postal_code}"

            kitchen_addr = f"{kitchen.address_line1}, {kitchen.city} - {kitchen.postal_code}" if kitchen else "Cloud Kitchen"

            pay = order.payments[0] if (hasattr(order, "payments") and order.payments) else None
            pay_method = pay.payment_method.value if pay else "UPI"
            pay_status = pay.payment_status.value if pay else "PENDING"

            items.append(
                DeliveryAssignmentItem(
                    delivery_id=d.delivery_id,
                    order_id=order.order_id,
                    order_number=order.order_number,
                    delivery_status=d.delivery_status,
                    order_status=order.order_status,
                    kitchen_name=kitchen.name if kitchen else "Kitchen",
                    kitchen_address=kitchen_addr,
                    kitchen_phone=kitchen.contact_phone if kitchen else None,
                    delivery_address=addr,
                    customer_name=cust_name,
                    customer_phone=cust_phone,
                    total_amount=order.total_amount,
                    payment_method=pay_method,
                    payment_status=pay_status,
                    assigned_at=d.assigned_at,
                    picked_up_at=d.picked_up_at,
                    delivered_at=d.delivered_at,
                )
            )

        return items, total

    @staticmethod
    def get_assignment_detail(
        db: Session, driver_ctx: DeliveryContext, delivery_id: int
    ) -> DeliveryAssignmentDetail:
        d = DeliveryRepository.get_delivery_by_id(db, delivery_id)
        if not d:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery assignment ID {delivery_id} not found",
            )

        # Cross-driver isolation: Driver can only view their own assignments
        if d.delivery_person_id != driver_ctx.delivery_person_id and driver_ctx.user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access: this delivery assignment is assigned to another courier",
            )

        order = d.order
        kitchen = order.kitchen
        cust_user = order.customer.user if (order.customer and hasattr(order.customer, "user")) else None
        cust_name = f"{cust_user.first_name} {cust_user.last_name}" if cust_user else "Customer"
        cust_phone = cust_user.phone_number if cust_user else None

        addr = "Takeaway / Dine-in"
        if order.delivery_address:
            addr = f"{order.delivery_address.address_line1}, {order.delivery_address.city} - {order.delivery_address.postal_code}"

        kitchen_addr = f"{kitchen.address_line1}, {kitchen.city} - {kitchen.postal_code}" if kitchen else "Cloud Kitchen"

        pay = order.payments[0] if (hasattr(order, "payments") and order.payments) else None
        pay_method = pay.payment_method.value if pay else "UPI"
        pay_status = pay.payment_status.value if pay else "PENDING"

        item_summaries = [
            DeliveryItemSummary(
                item_name=itm.item_name_snapshot,
                quantity=itm.quantity,
            )
            for itm in (order.order_items or [])
        ]

        return DeliveryAssignmentDetail(
            delivery_id=d.delivery_id,
            order_id=order.order_id,
            order_number=order.order_number,
            delivery_status=d.delivery_status,
            order_status=order.order_status,
            kitchen_id=order.kitchen_id,
            kitchen_name=kitchen.name if kitchen else "Kitchen",
            kitchen_address=kitchen_addr,
            kitchen_phone=kitchen.contact_phone if kitchen else None,
            delivery_address=addr,
            customer_name=cust_name,
            customer_phone=cust_phone,
            items=item_summaries,
            total_amount=order.total_amount,
            payment_method=pay_method,
            payment_status=pay_status,
            special_instructions=order.special_instructions,
            delivery_notes=d.delivery_notes,
            delivery_otp=d.delivery_otp,
            assigned_at=d.assigned_at,
            picked_up_at=d.picked_up_at,
            delivered_at=d.delivered_at,
        )

    @staticmethod
    def update_delivery_status(
        db: Session, driver_ctx: DeliveryContext, delivery_id: int, data: DeliveryStatusUpdate
    ) -> DeliveryAssignmentDetail:
        d = DeliveryRepository.get_delivery_by_id(db, delivery_id)
        if not d:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery assignment ID {delivery_id} not found",
            )

        if d.delivery_person_id != driver_ctx.delivery_person_id and driver_ctx.user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access: this delivery assignment belongs to another courier",
            )

        order = d.order
        now = datetime.utcnow()
        current_del_status = d.delivery_status
        target_del_status = data.status

        # -----------------------------------------------------
        # State Machine Transition Rules
        # ASSIGNED -> PICKED_UP -> OUT_FOR_DELIVERY -> DELIVERED
        # -----------------------------------------------------
        if target_del_status == DeliveryStatus.PICKED_UP:
            if current_del_status != DeliveryStatus.ASSIGNED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot mark picked up from current status {current_del_status}",
                )

            # Prevent driver from marking picked up before the order is ready in the kitchen
            if order.order_status not in [OrderStatus.READY_FOR_PICKUP, OrderStatus.OUT_FOR_DELIVERY]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Order #{order.order_number} is currently in '{order.order_status.value}' state. "
                        "Cannot pick up before kitchen expediter marks ticket READY_FOR_PICKUP."
                    ),
                )

            d.delivery_status = DeliveryStatus.PICKED_UP
            d.picked_up_at = now
            if data.notes:
                d.delivery_notes = data.notes

            # Keep driver as ON_DELIVERY
            driver_ctx.delivery_person.current_status = DeliveryPersonStatus.ON_DELIVERY

            # Log history
            hist = OrderStatusHistory(
                order_id=order.order_id,
                changed_by_user_id=driver_ctx.user.user_id,
                previous_status=order.order_status,
                new_status=OrderStatus.READY_FOR_PICKUP,
                notes=f"Courier picked up order from kitchen. {data.notes or ''}".strip(),
            )
            db.add(hist)

        elif target_del_status == DeliveryStatus.OUT_FOR_DELIVERY:
            if current_del_status not in [DeliveryStatus.ASSIGNED, DeliveryStatus.PICKED_UP]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot transition to OUT_FOR_DELIVERY from {current_del_status}",
                )

            d.delivery_status = DeliveryStatus.OUT_FOR_DELIVERY
            if not d.picked_up_at:
                d.picked_up_at = now
            if data.notes:
                d.delivery_notes = data.notes

            old_order_status = order.order_status
            order.order_status = OrderStatus.OUT_FOR_DELIVERY
            driver_ctx.delivery_person.current_status = DeliveryPersonStatus.ON_DELIVERY

            hist = OrderStatusHistory(
                order_id=order.order_id,
                changed_by_user_id=driver_ctx.user.user_id,
                previous_status=old_order_status,
                new_status=OrderStatus.OUT_FOR_DELIVERY,
                notes=data.notes or "Courier is in transit to delivery destination",
            )
            db.add(hist)

        elif target_del_status == DeliveryStatus.DELIVERED:
            # Prevent duplicate completion
            if current_del_status == DeliveryStatus.DELIVERED or order.order_status == OrderStatus.DELIVERED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order #{order.order_number} is already marked as DELIVERED",
                )

            # Prevent marking delivered without prior eligible transit status
            if current_del_status not in [DeliveryStatus.OUT_FOR_DELIVERY, DeliveryStatus.PICKED_UP]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot complete delivery directly from '{current_del_status}'. Order must be OUT_FOR_DELIVERY.",
                )

            # Optional OTP verification check if configured
            if d.delivery_otp and data.delivery_otp:
                if d.delivery_otp.strip() != data.delivery_otp.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid delivery OTP provided by customer",
                    )

            d.delivery_status = DeliveryStatus.DELIVERED
            d.delivered_at = now
            if data.notes:
                d.delivery_notes = data.notes
            if data.signature_url:
                d.customer_signature_url = data.signature_url

            old_order_status = order.order_status
            order.order_status = OrderStatus.DELIVERED

            # Free the delivery person back to AVAILABLE status
            driver_ctx.delivery_person.current_status = DeliveryPersonStatus.AVAILABLE

            hist = OrderStatusHistory(
                order_id=order.order_id,
                changed_by_user_id=driver_ctx.user.user_id,
                previous_status=old_order_status,
                new_status=OrderStatus.DELIVERED,
                notes=data.notes or "Handoff completed successfully to customer",
            )
            db.add(hist)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported status transition: {target_del_status}",
            )

        db.commit()
        db.refresh(d)

        # Invalidate tracking cache in Redis
        try:
            redis_client.delete(f"order:tracking:{order.order_id}")
            redis_client.delete(f"order:{order.order_id}:status")
        except Exception:
            pass

        return DeliveryService.get_assignment_detail(db, driver_ctx, delivery_id)

    # -----------------------------------------------------
    # Status-Based Order Tracking (Customer / Driver / Admin)
    # -----------------------------------------------------
    @staticmethod
    def get_order_tracking(db: Session, order_id: int, current_user: User) -> OrderTrackingOut:
        order = (
            db.query(Order)
            .options(
                joinedload(Order.customer),
                joinedload(Order.kitchen),
                joinedload(Order.delivery_address),
                joinedload(Order.delivery).joinedload(Delivery.delivery_person).joinedload(DeliveryPerson.user),
                joinedload(Order.status_history),
            )
            .filter(Order.order_id == order_id)
            .first()
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order ID {order_id} not found",
            )

        # Access Authorization: Must be order customer, assigned driver, or admin
        is_customer = order.customer_id == current_user.user_id
        is_assigned_driver = (
            order.delivery and order.delivery.delivery_person_id == current_user.user_id
        )
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_customer or is_assigned_driver or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access: you cannot view tracking for another customer's order",
            )

        # Check Redis Cache
        cache_key = f"order:tracking:{order_id}"
        cached = redis_client.get_json(cache_key)
        if cached:
            return OrderTrackingOut(**cached)

        delivery = order.delivery
        driver = delivery.delivery_person if delivery else None
        driver_user = driver.user if driver else None

        timeline = [
            TrackingStatusPoint(
                status=h.new_status.value if hasattr(h.new_status, "value") else str(h.new_status),
                changed_at=h.created_at,
                notes=h.notes,
            )
            for h in (order.status_history or [])
        ]
        # Sort chronologically
        timeline.sort(key=lambda x: x.changed_at)

        addr = "Takeaway"
        if order.delivery_address:
            addr = f"{order.delivery_address.address_line1}, {order.delivery_address.city} - {order.delivery_address.postal_code}"

        kitchen_addr = f"{order.kitchen.address_line1}, {order.kitchen.city}" if order.kitchen else "Kitchen"

        tracking_data = OrderTrackingOut(
            order_id=order.order_id,
            order_number=order.order_number,
            order_status=order.order_status,
            delivery_status=delivery.delivery_status if delivery else None,
            kitchen_name=order.kitchen.name if order.kitchen else "Kitchen",
            kitchen_address=kitchen_addr,
            delivery_address=addr,
            delivery_person_name=f"{driver_user.first_name}" if driver_user else None,
            delivery_person_phone=driver_user.phone_number if (driver_user and (is_customer or is_admin)) else None,
            vehicle_type=driver.vehicle_type if driver else None,
            vehicle_number=driver.vehicle_number if driver else None,
            timeline=timeline,
            created_at=order.placed_at,
            estimated_delivery_time=order.estimated_delivery_time,
        )

        try:
            payload = tracking_data.model_dump(mode="json")
            redis_client.set_json(cache_key, payload, ex=60)
            redis_client.set_json(f"order:{order_id}:status", payload, ex=60)
        except Exception:
            pass

        return tracking_data

    # -----------------------------------------------------
    # Administrator-Authorized Delivery Assignment
    # -----------------------------------------------------
    @staticmethod
    def get_available_personnel(db: Session) -> List[AvailablePersonnelOut]:
        drivers = DeliveryRepository.get_available_personnel(db)
        out = []
        for d in drivers:
            user = d.user
            out.append(
                AvailablePersonnelOut(
                    delivery_person_id=d.delivery_person_id,
                    full_name=f"{user.first_name} {user.last_name}",
                    phone=user.phone_number,
                    vehicle_type=d.vehicle_type,
                    vehicle_number=d.vehicle_number,
                    rating=d.rating,
                    current_status=d.current_status,
                )
            )
        return out

    @staticmethod
    def assign_delivery_to_order(
        db: Session, order_id: int, delivery_person_id: int, admin_user_id: int
    ) -> DeliveryAssignmentDetail:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order ID {order_id} does not exist",
            )

        # Order eligibility check: cannot assign delivery to cancelled or delivered orders
        if order.order_status in [OrderStatus.CANCELLED, OrderStatus.DELIVERED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot dispatch delivery for order in '{order.order_status.value}' state",
            )

        # Driver eligibility check
        driver = db.query(DeliveryPerson).join(DeliveryPerson.user).filter(
            DeliveryPerson.delivery_person_id == delivery_person_id,
            User.is_active == True,
        ).first()

        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Delivery personnel ID {delivery_person_id} not found or account is deactivated",
            )

        if driver.current_status == DeliveryPersonStatus.OFF_DUTY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Courier {driver.user.first_name} is currently OFF_DUTY and unavailable for dispatch",
            )

        # Prevent duplicate / conflicting assignments if driver already has an active order
        conflicting_delivery = (
            db.query(Delivery)
            .filter(
                Delivery.delivery_person_id == delivery_person_id,
                Delivery.order_id != order_id,
                Delivery.delivery_status.in_([DeliveryStatus.ASSIGNED, DeliveryStatus.PICKED_UP, DeliveryStatus.OUT_FOR_DELIVERY]),
            )
            .first()
        )
        if conflicting_delivery:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Courier {driver.user.first_name} already has active Order #{conflicting_delivery.order_id} in progress. "
                    "Cannot assign conflicting deliveries."
                ),
            )

        # Prevent duplicate assignment on the same order if already assigned and active
        existing_del = db.query(Delivery).filter(Delivery.order_id == order_id).first()
        if existing_del and existing_del.delivery_status in [DeliveryStatus.PICKED_UP, DeliveryStatus.OUT_FOR_DELIVERY]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order #{order.order_number} is already in transit with courier #{existing_del.delivery_person_id}",
            )

        # Generate secure 4-digit delivery handoff OTP
        otp_code = str(random.randint(1000, 9999))

        delivery = DeliveryRepository.create_or_assign_delivery(
            db=db,
            order_id=order_id,
            delivery_person_id=delivery_person_id,
            delivery_otp=otp_code,
        )

        driver.current_status = DeliveryPersonStatus.ON_DELIVERY

        # Record admin audit log
        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="ASSIGN_DELIVERY",
            entity_type="ORDER",
            entity_id=order_id,
            details={
                "order_number": order.order_number,
                "delivery_person_id": delivery_person_id,
                "driver_name": f"{driver.user.first_name} {driver.user.last_name}",
            },
        )

        db.commit()
        db.refresh(delivery)

        # Invalidate cache
        try:
            redis_client.delete(f"order:tracking:{order_id}")
            redis_client.delete(f"order:{order_id}:status")
        except Exception:
            pass

        # Load full detail using a temporary driver context for presentation
        driver_ctx = DeliveryContext(
            user=driver.user,
            delivery_person=driver,
            delivery_person_id=driver.delivery_person_id,
            current_status=driver.current_status,
        )
        return DeliveryService.get_assignment_detail(db, driver_ctx, delivery.delivery_id)
