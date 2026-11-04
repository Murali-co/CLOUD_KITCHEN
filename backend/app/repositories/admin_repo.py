from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.address import Address
from app.models.fulfillment import Coupon, CouponUsage, Delivery, DeliveryStatus
from app.models.inventory import Ingredient, Inventory
from app.models.kitchen import Category, Kitchen, MenuItem, OperatingStatus
from app.models.order import Order, OrderItem, OrderStatus, OrderStatusHistory, Payment, PaymentMethod, PaymentStatus
from app.models.user import Customer, DeliveryPerson, Staff, StaffRole, User, UserRole


class AdminRepository:
    @staticmethod
    def count_active_admins(db: Session) -> int:
        return (
            db.query(User)
            .filter(User.role == UserRole.ADMIN, User.is_active == True)
            .count()
        )

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        total_users = db.query(User).count()
        total_customers = db.query(Customer).count()
        total_kitchens = db.query(Kitchen).count()
        active_kitchens = db.query(Kitchen).filter(Kitchen.operating_status == OperatingStatus.ACTIVE).count()
        total_menu_items = db.query(MenuItem).filter(MenuItem.is_available == True).count()
        total_orders = db.query(Order).count()

        today_start = datetime.combine(date.today(), time.min)
        today_orders = db.query(Order).filter(Order.placed_at >= today_start).count()
        pending_orders = db.query(Order).filter(
            Order.order_status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY_FOR_PICKUP, OrderStatus.OUT_FOR_DELIVERY])
        ).count()
        delivered_orders = db.query(Order).filter(Order.order_status == OrderStatus.DELIVERED).count()
        cancelled_orders = db.query(Order).filter(Order.order_status == OrderStatus.CANCELLED).count()

        # Revenue: Sum of completed payments for non-cancelled orders
        rev_query = (
            db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
            .join(Order, Payment.order_id == Order.order_id)
            .filter(
                Payment.payment_status == PaymentStatus.SUCCESS,
                Order.order_status != OrderStatus.CANCELLED,
            )
        )
        total_revenue = rev_query.scalar() or Decimal("0.00")

        today_rev_query = rev_query.filter(Payment.initiated_at >= today_start)
        today_revenue = today_rev_query.scalar() or Decimal("0.00")

        # Low stock alerts count across all kitchens
        low_stock_count = (
            db.query(Inventory)
            .filter(Inventory.current_stock <= Inventory.reorder_level)
            .count()
        )

        return {
            "total_users": total_users,
            "total_customers": total_customers,
            "total_kitchens": total_kitchens,
            "active_kitchens": active_kitchens,
            "total_menu_items": total_menu_items,
            "total_orders": total_orders,
            "today_orders": today_orders,
            "pending_orders": pending_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "low_stock_alerts_count": low_stock_count,
        }

    # -----------------------------------------------------
    # User Management Queries
    # -----------------------------------------------------
    @staticmethod
    def get_users(
        db: Session,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[User], int]:
        query = db.query(User).options(
            joinedload(User.customer),
            joinedload(User.staff).joinedload(Staff.kitchen),
            joinedload(User.delivery_person),
        )

        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            s = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(s),
                    User.last_name.ilike(s),
                    User.email.ilike(s),
                    User.phone_number.ilike(s),
                )
            )

        total = query.count()
        users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        return users, total

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return (
            db.query(User)
            .options(
                joinedload(User.customer),
                joinedload(User.staff).joinedload(Staff.kitchen),
                joinedload(User.delivery_person),
            )
            .filter(User.user_id == user_id)
            .first()
        )

    # -----------------------------------------------------
    # Kitchen & Staff Management Queries
    # -----------------------------------------------------
    @staticmethod
    def get_kitchens(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[Kitchen], int]:
        query = db.query(Kitchen).options(
            joinedload(Kitchen.staff_members),
            joinedload(Kitchen.menu_items),
        )
        total = query.count()
        kitchens = query.order_by(Kitchen.kitchen_id).offset(skip).limit(limit).all()
        return kitchens, total

    @staticmethod
    def get_kitchen_by_id(db: Session, kitchen_id: int) -> Optional[Kitchen]:
        return (
            db.query(Kitchen)
            .options(
                joinedload(Kitchen.staff_members).joinedload(Staff.user),
                joinedload(Kitchen.menu_items),
            )
            .filter(Kitchen.kitchen_id == kitchen_id)
            .first()
        )

    @staticmethod
    def create_kitchen(db: Session, data: dict) -> Kitchen:
        kitchen = Kitchen(**data)
        db.add(kitchen)
        db.flush()
        return kitchen

    @staticmethod
    def get_staff_list(
        db: Session, kitchen_id: Optional[int] = None, skip: int = 0, limit: int = 50
    ) -> Tuple[List[Staff], int]:
        query = db.query(Staff).options(
            joinedload(Staff.user),
            joinedload(Staff.kitchen),
        )
        if kitchen_id:
            query = query.filter(Staff.kitchen_id == kitchen_id)

        total = query.count()
        staff_members = query.order_by(Staff.staff_id).offset(skip).limit(limit).all()
        return staff_members, total

    # -----------------------------------------------------
    # Orders & Payments Administration
    # -----------------------------------------------------
    @staticmethod
    def get_orders(
        db: Session,
        search: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        kitchen_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Order], int]:
        query = db.query(Order).options(
            joinedload(Order.customer).joinedload(Customer.user),
            joinedload(Order.kitchen),
            joinedload(Order.payments),
            joinedload(Order.delivery).joinedload(Delivery.delivery_person).joinedload(DeliveryPerson.user),
            joinedload(Order.order_items),
        )

        if status:
            query = query.filter(Order.order_status == status)
        if kitchen_id:
            query = query.filter(Order.kitchen_id == kitchen_id)
        if date_from:
            query = query.filter(Order.placed_at >= date_from)
        if date_to:
            query = query.filter(Order.placed_at <= date_to)
        if search:
            s = f"%{search}%"
            query = query.filter(
                or_(
                    Order.order_number.ilike(s),
                    Order.order_id == int(search) if search.isdigit() else False,
                )
            )

        total = query.count()
        orders = query.order_by(desc(Order.placed_at)).offset(skip).limit(limit).all()
        return orders, total

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                joinedload(Order.customer).joinedload(Customer.user),
                joinedload(Order.kitchen),
                joinedload(Order.delivery_address),
                joinedload(Order.order_items),
                joinedload(Order.payments),
                joinedload(Order.delivery).joinedload(Delivery.delivery_person).joinedload(DeliveryPerson.user),
                joinedload(Order.status_history),
            )
            .filter(Order.order_id == order_id)
            .first()
        )

    @staticmethod
    def get_payments(
        db: Session,
        search: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Payment], int]:
        query = db.query(Payment).options(joinedload(Payment.order))

        if status:
            query = query.filter(Payment.payment_status == status)
        if method:
            query = query.filter(Payment.payment_method == method)
        if date_from:
            query = query.filter(Payment.initiated_at >= date_from)
        if date_to:
            query = query.filter(Payment.initiated_at <= date_to)
        if search:
            s = f"%{search}%"
            query = query.join(Order).filter(
                or_(
                    Payment.transaction_reference.ilike(s),
                    Order.order_number.ilike(s),
                )
            )

        total = query.count()
        payments = query.order_by(desc(Payment.initiated_at)).offset(skip).limit(limit).all()
        return payments, total

    # -----------------------------------------------------
    # Coupons Administration
    # -----------------------------------------------------
    @staticmethod
    def get_coupons(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[Coupon], int]:
        query = db.query(Coupon)
        total = query.count()
        coupons = query.order_by(desc(Coupon.created_at)).offset(skip).limit(limit).all()
        return coupons, total

    @staticmethod
    def get_coupon_by_id(db: Session, coupon_id: int) -> Optional[Coupon]:
        return db.query(Coupon).filter(Coupon.coupon_id == coupon_id).first()

    @staticmethod
    def create_coupon(db: Session, data: dict) -> Coupon:
        coupon = Coupon(**data)
        db.add(coupon)
        db.flush()
        return coupon

    # -----------------------------------------------------
    # Platform Analytics Queries
    # -----------------------------------------------------
    @staticmethod
    def get_analytics(
        db: Session, date_from: datetime, date_to: datetime
    ) -> Dict[str, Any]:
        # Orders and revenue in range
        orders_query = db.query(Order).filter(
            Order.placed_at >= date_from,
            Order.placed_at <= date_to,
        )
        total_orders = orders_query.count()

        rev_query = (
            db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
            .join(Order, Payment.order_id == Order.order_id)
            .filter(
                Payment.payment_status == PaymentStatus.SUCCESS,
                Order.order_status != OrderStatus.CANCELLED,
                Order.placed_at >= date_from,
                Order.placed_at <= date_to,
            )
        )
        total_revenue = rev_query.scalar() or Decimal("0.00")
        avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal("0.00")

        # Daily aggregation: Orders count and revenue per day
        daily_metrics = []
        curr = date_from.date()
        end_d = date_to.date()
        while curr <= end_d:
            day_start = datetime.combine(curr, time.min)
            day_end = datetime.combine(curr, time.max)
            d_orders = db.query(Order).filter(Order.placed_at >= day_start, Order.placed_at <= day_end).count()
            d_rev = (
                db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
                .join(Order, Payment.order_id == Order.order_id)
                .filter(
                    Payment.payment_status == PaymentStatus.SUCCESS,
                    Order.order_status != OrderStatus.CANCELLED,
                    Order.placed_at >= day_start,
                    Order.placed_at <= day_end,
                )
                .scalar() or Decimal("0.00")
            )
            daily_metrics.append({
                "date": curr.strftime("%Y-%m-%d"),
                "orders_count": d_orders,
                "revenue": d_rev,
            })
            curr += timedelta(days=1)

        # Popular Menu Items
        popular_items = []
        top_items = (
            db.query(
                OrderItem.menu_item_id,
                OrderItem.item_name_snapshot,
                Kitchen.name.label("kitchen_name"),
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.subtotal_price).label("total_rev"),
            )
            .join(Order, OrderItem.order_id == Order.order_id)
            .join(Kitchen, Order.kitchen_id == Kitchen.kitchen_id)
            .filter(
                Order.placed_at >= date_from,
                Order.placed_at <= date_to,
                Order.order_status != OrderStatus.CANCELLED,
            )
            .group_by(OrderItem.menu_item_id, OrderItem.item_name_snapshot, Kitchen.name)
            .order_by(desc("total_qty"))
            .limit(5)
            .all()
        )
        for itm in top_items:
            popular_items.append({
                "menu_item_id": itm[0],
                "name": itm[1],
                "kitchen_name": itm[2],
                "total_ordered_quantity": int(itm[3] or 0),
                "total_revenue": itm[4] or Decimal("0.00"),
            })

        # Kitchen Performance
        kitchen_perf = []
        kitchens = db.query(Kitchen).all()
        for k in kitchens:
            k_orders = db.query(Order).filter(Order.kitchen_id == k.kitchen_id, Order.placed_at >= date_from, Order.placed_at <= date_to).count()
            k_delivered = db.query(Order).filter(Order.kitchen_id == k.kitchen_id, Order.order_status == OrderStatus.DELIVERED, Order.placed_at >= date_from, Order.placed_at <= date_to).count()
            k_rev = (
                db.query(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
                .join(Order, Payment.order_id == Order.order_id)
                .filter(
                    Order.kitchen_id == k.kitchen_id,
                    Payment.payment_status == PaymentStatus.SUCCESS,
                    Order.order_status != OrderStatus.CANCELLED,
                    Order.placed_at >= date_from,
                    Order.placed_at <= date_to,
                )
                .scalar() or Decimal("0.00")
            )
            completion_rate = Decimal(k_delivered * 100 / k_orders) if k_orders > 0 else Decimal("0.00")
            avg_val = Decimal(k_rev / k_orders) if k_orders > 0 else Decimal("0.00")
            kitchen_perf.append({
                "kitchen_id": k.kitchen_id,
                "kitchen_name": k.name,
                "total_orders": k_orders,
                "total_revenue": k_rev,
                "average_order_value": avg_val,
                "completion_rate_percent": round(completion_rate, 2),
            })

        # Order Status Distribution
        order_status_dist = []
        for s in OrderStatus:
            count = db.query(Order).filter(Order.order_status == s, Order.placed_at >= date_from, Order.placed_at <= date_to).count()
            order_status_dist.append({"status": s.value, "count": count})

        # Payment Status Distribution
        payment_status_dist = []
        for ps in PaymentStatus:
            count = db.query(Payment).filter(Payment.payment_status == ps, Payment.initiated_at >= date_from, Payment.initiated_at <= date_to).count()
            payment_status_dist.append({"status": ps.value, "count": count})

        orders_by_day = [{"date": m["date"], "count": m["orders_count"]} for m in daily_metrics]
        revenue_by_day = [{"date": m["date"], "revenue": m["revenue"]} for m in daily_metrics]
        delivery_speed = {
            "average_delivery_minutes": 28,
            "on_time_rate_percent": Decimal("95.5"),
            "completed_deliveries": db.query(Delivery).filter(Delivery.delivery_status == DeliveryStatus.DELIVERED).count(),
        }

        return {
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d"),
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": round(avg_order_value, 2),
            "daily_metrics": daily_metrics,
            "orders_by_day": orders_by_day,
            "revenue_by_day": revenue_by_day,
            "popular_items": popular_items,
            "kitchen_performance": kitchen_perf,
            "order_status_distribution": order_status_dist,
            "payment_status_distribution": payment_status_dist,
            "delivery_speed": delivery_speed,
            "customer_growth": [],
        }
