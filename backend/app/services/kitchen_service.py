import json
from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import StaffContext
from app.db.redis import redis_client
from app.models.kitchen import Kitchen, OperatingStatus, MenuItem
from app.models.order import Order, OrderStatus, PaymentStatus, PaymentMethod
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.kitchen_repo import CategoryRepository, KitchenRepository, MenuRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.category import CategoryResponse
from app.schemas.kitchen import KitchenDetailResponse, KitchenResponse
from app.schemas.kitchen_management import (
    KitchenAvailabilityOut,
    KitchenAvailabilityUpdate,
    KitchenDashboardStats,
    KitchenMenuItemCreate,
    KitchenMenuItemOut,
    KitchenMenuItemUpdate,
    KitchenOrderDetail,
    KitchenOrderItemOut,
    KitchenOrderListItem,
    KitchenOrderStatusHistoryOut,
    KitchenOrderStatusUpdate,
    KitchenQueueItem,
    RecentOrderActivity,
    StaffProfileOut,
)
from app.schemas.menu import MenuItemDetailResponse, MenuItemResponse
from app.services.inventory_service import InventoryService


class KitchenService:
    # -----------------------------------------------------
    # Public / Customer Kitchen Browsing (Phase 4/5)
    # -----------------------------------------------------
    @staticmethod
    def list_kitchens(
        db: Session,
        search: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        skip = (page - 1) * page_size
        kitchens, total = KitchenRepository.get_active_kitchens(
            db, search=search, city=city, skip=skip, limit=page_size
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        items = [KitchenResponse.model_validate(k) for k in kitchens]
        return {
            "items": items,
            "meta": {
                "total_count": total,
                "page": page,
                "page_size": page_size,
                "total_records": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    @staticmethod
    def get_kitchen_detail(db: Session, kitchen_id: int) -> KitchenDetailResponse:
        kitchen = KitchenRepository.get_by_id(db, kitchen_id)
        if not kitchen:
            raise HTTPException(status_code=404, detail="Kitchen branch not found")
        resp = KitchenDetailResponse.model_validate(kitchen)
        resp.menu_items_count = len(kitchen.menu_items)
        return resp

    # -----------------------------------------------------
    # Staff Profile & Access Verification
    # -----------------------------------------------------
    @staticmethod
    def get_staff_profile(staff_ctx: StaffContext, db: Session) -> StaffProfileOut:
        kitchen = KitchenRepository.get_by_id(db, staff_ctx.kitchen_id)
        if not kitchen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kitchen facility ID {staff_ctx.kitchen_id} does not exist",
            )

        hired = staff_ctx.staff.hired_date if staff_ctx.staff else datetime.utcnow().date()
        shift = staff_ctx.staff.shift_timing.value if staff_ctx.staff else "MORNING"

        return StaffProfileOut(
            staff_id=staff_ctx.user.user_id,
            kitchen_id=staff_ctx.kitchen_id,
            staff_role=staff_ctx.staff_role,
            kitchen_name=kitchen.name,
            branch_code=kitchen.branch_code,
            shift_timing=shift,
            hired_date=hired,
        )

    # -----------------------------------------------------
    # Kitchen Dashboard Statistics
    # -----------------------------------------------------
    @staticmethod
    def get_dashboard_stats(db: Session, staff_ctx: StaffContext) -> KitchenDashboardStats:
        kitchen = KitchenRepository.get_by_id(db, staff_ctx.kitchen_id)
        if not kitchen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kitchen facility not found",
            )

        counts = OrderRepository.get_kitchen_dashboard_stats(db, staff_ctx.kitchen_id)
        low_stock_count = InventoryRepository.count_low_stock(db, staff_ctx.kitchen_id)

        active_orders = counts["confirmed"] + counts["preparing"] + counts["ready"]
        max_active = kitchen.max_active_orders if kitchen.max_active_orders > 0 else 50
        capacity_pct = min(100.0, round((active_orders / max_active) * 100.0, 1))

        recent_activity: List[RecentOrderActivity] = []
        for o in counts["recent_orders"]:
            cust_name = (
                f"{o.customer.user.first_name} {o.customer.user.last_name}"
                if o.customer and o.customer.user
                else "Guest Customer"
            )
            recent_activity.append(
                RecentOrderActivity(
                    order_id=o.order_id,
                    order_number=o.order_number,
                    status=o.order_status,
                    total_amount=o.total_amount,
                    placed_at=o.placed_at,
                    customer_name=cust_name,
                )
            )

        return KitchenDashboardStats(
            kitchen_id=kitchen.kitchen_id,
            kitchen_name=kitchen.name,
            operating_status=kitchen.operating_status,
            total_orders_today=counts["total_today"],
            new_orders=counts["new_orders"],
            confirmed_orders=counts["confirmed"],
            preparing_orders=counts["preparing"],
            ready_orders=counts["ready"],
            completed_orders=counts["completed_today"],
            cancelled_orders=counts["cancelled_today"],
            active_orders_count=active_orders,
            max_active_orders=max_active,
            capacity_percentage=capacity_pct,
            low_stock_count=low_stock_count,
            recent_activity=recent_activity,
        )

    # -----------------------------------------------------
    # Kitchen Orders & Queue Management
    # -----------------------------------------------------
    @staticmethod
    def get_orders(
        db: Session,
        staff_ctx: StaffContext,
        status_filter: Optional[OrderStatus] = None,
        date_filter: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[KitchenOrderListItem], int]:
        orders, total = OrderRepository.get_kitchen_orders(
            db=db,
            kitchen_id=staff_ctx.kitchen_id,
            status=status_filter,
            date_filter=date_filter,
            search=search,
            skip=skip,
            limit=limit,
        )

        items_out = []
        for o in orders:
            cust_name = (
                f"{o.customer.user.first_name} {o.customer.user.last_name}"
                if o.customer and o.customer.user
                else "Customer"
            )
            cust_phone = (
                o.customer.user.phone_number
                if o.customer and o.customer.user
                else "N/A"
            )
            latest_payment = o.payments[-1] if o.payments else None
            p_status = latest_payment.payment_status if latest_payment else PaymentStatus.PENDING
            p_method = latest_payment.payment_method if latest_payment else PaymentMethod.UPI

            items_out.append(
                KitchenOrderListItem(
                    order_id=o.order_id,
                    order_number=o.order_number,
                    customer_id=o.customer_id,
                    customer_name=cust_name,
                    customer_phone=cust_phone,
                    order_status=o.order_status,
                    subtotal_amount=o.subtotal_amount,
                    total_amount=o.total_amount,
                    payment_status=p_status,
                    payment_method=p_method,
                    placed_at=o.placed_at,
                    item_count=len(o.order_items),
                    special_instructions=o.special_instructions,
                )
            )

        return items_out, total

    @staticmethod
    def get_order_detail(
        db: Session, staff_ctx: StaffContext, order_id: int
    ) -> KitchenOrderDetail:
        order = OrderRepository.get_kitchen_order_by_id(
            db=db, order_id=order_id, kitchen_id=staff_ctx.kitchen_id
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order #{order_id} not found in your assigned kitchen facility",
            )

        cust_name = (
            f"{order.customer.user.first_name} {order.customer.user.last_name}"
            if order.customer and order.customer.user
            else "Customer"
        )
        cust_phone = (
            order.customer.user.phone_number
            if order.customer and order.customer.user
            else "N/A"
        )

        addr_str = "Customer Pickup"
        if order.delivery_address:
            addr = order.delivery_address
            addr_str = f"{addr.address_line1}, {addr.city}, {addr.state} - {addr.postal_code} (Phone: {addr.recipient_phone})"

        latest_payment = order.payments[-1] if order.payments else None
        p_status = latest_payment.payment_status if latest_payment else PaymentStatus.PENDING
        p_method = latest_payment.payment_method if latest_payment else PaymentMethod.UPI

        items_out = [
            KitchenOrderItemOut(
                order_item_id=i.order_item_id,
                menu_item_id=i.menu_item_id,
                item_name=i.item_name_snapshot,
                unit_price=i.unit_price_snapshot,
                quantity=i.quantity,
                subtotal=i.subtotal_price,
                customization_notes=i.customization_notes,
            )
            for i in order.order_items
        ]

        timeline_out = []
        for h in sorted(order.status_history, key=lambda x: x.created_at):
            changer_name = (
                f"{h.changed_by_user.first_name} {h.changed_by_user.last_name}"
                if h.changed_by_user
                else "System"
            )
            timeline_out.append(
                KitchenOrderStatusHistoryOut(
                    history_id=h.history_id,
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    changed_by_user_id=h.changed_by_user_id,
                    changed_by_name=changer_name,
                    notes=h.notes,
                    created_at=h.created_at,
                )
            )

        return KitchenOrderDetail(
            order_id=order.order_id,
            order_number=order.order_number,
            kitchen_id=order.kitchen_id,
            customer_id=order.customer_id,
            customer_name=cust_name,
            customer_phone=cust_phone,
            delivery_address=addr_str,
            order_status=order.order_status,
            payment_status=p_status,
            payment_method=p_method,
            subtotal_amount=order.subtotal_amount,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            delivery_fee=order.delivery_fee,
            total_amount=order.total_amount,
            special_instructions=order.special_instructions,
            placed_at=order.placed_at,
            items=items_out,
            timeline=timeline_out,
        )

    @staticmethod
    def update_order_status(
        db: Session,
        staff_ctx: StaffContext,
        order_id: int,
        data: KitchenOrderStatusUpdate,
    ) -> KitchenOrderDetail:
        order = OrderRepository.get_kitchen_order_by_id(
            db=db, order_id=order_id, kitchen_id=staff_ctx.kitchen_id
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order #{order_id} not found in your assigned kitchen",
            )

        current_status = order.order_status
        target_status = data.status

        # Idempotent response if already in requested state
        if current_status == target_status:
            return KitchenService.get_order_detail(db, staff_ctx, order_id)

        # Explicit prohibition: Kitchen staff cannot mark DELIVERED
        if target_status == OrderStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Kitchen staff are not authorized to mark orders as DELIVERED. "
                    "Delivery personnel must confirm physical handover."
                ),
            )

        # Enforce terminal state immutability
        if current_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status of an order that is already {current_status.value}",
            )

        # Authorized state transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED],
            OrderStatus.READY_FOR_PICKUP: [OrderStatus.CANCELLED],
        }

        allowed = valid_transitions.get(current_status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition from {current_status.value} to {target_status.value}. "
                    f"Allowed next states: {[s.value for s in allowed]}"
                ),
            )

        # If transitioning to PREPARING -> Trigger Atomic Recipe Inventory Deduction!
        if target_status == OrderStatus.PREPARING:
            InventoryService.deduct_inventory_for_order(
                db=db, order=order, acting_user_id=staff_ctx.user.user_id
            )

        # Record status update and audit trail
        OrderRepository.update_status(
            db=db,
            order=order,
            new_status=target_status,
            changed_by_user_id=staff_ctx.user.user_id,
            notes=data.notes or f"Status updated to {target_status.value} by kitchen staff",
        )

        db.commit()

        # Invalidate Redis order queue and tracking caches
        try:
            redis_client.delete(f"kitchen:{staff_ctx.kitchen_id}:order_queue")
            redis_client.delete(f"order:{order_id}:status")
            redis_client.delete(f"order:tracking:{order_id}")
            redis_client.delete("admin:dashboard:metrics")
        except Exception:
            pass

        return KitchenService.get_order_detail(db, staff_ctx, order_id)

    @staticmethod
    def get_order_queue(db: Session, staff_ctx: StaffContext) -> List[KitchenQueueItem]:
        cache_key = f"kitchen:{staff_ctx.kitchen_id}:order_queue"
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return [KitchenQueueItem(**item) for item in data]
            except Exception:
                pass

        orders = OrderRepository.get_kitchen_queue(db, staff_ctx.kitchen_id)
        now = datetime.utcnow()

        queue_items: List[KitchenQueueItem] = []
        for o in orders:
            placed = o.placed_at
            age_minutes = max(0, int((now - placed).total_seconds() // 60))
            is_urgent = (
                (o.order_status in [OrderStatus.CONFIRMED, OrderStatus.PREPARING] and age_minutes >= 20)
                or (age_minutes >= 35)
            )
            cust_name = (
                f"{o.customer.user.first_name} {o.customer.user.last_name}"
                if o.customer and o.customer.user
                else "Customer"
            )
            summary = [
                f"{item.quantity}x {item.item_name_snapshot}"
                for item in o.order_items
            ]

            queue_items.append(
                KitchenQueueItem(
                    order_id=o.order_id,
                    order_number=o.order_number,
                    order_status=o.order_status,
                    placed_at=o.placed_at,
                    order_age_minutes=age_minutes,
                    is_urgent=is_urgent,
                    customer_name=cust_name,
                    items_summary=summary,
                    item_count=len(o.order_items),
                    special_instructions=o.special_instructions,
                )
            )

        # Cache in Redis with 30-second TTL
        try:
            dumped = json.dumps([item.model_dump(mode="json") for item in queue_items])
            redis_client.set(cache_key, dumped, ex=30)
        except Exception:
            pass

        return queue_items

    # -----------------------------------------------------
    # Kitchen Menu Management
    # -----------------------------------------------------
    @staticmethod
    def get_menu(
        db: Session,
        staff_ctx: StaffContext,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        is_available: Optional[bool] = None,
    ) -> List[KitchenMenuItemOut]:
        items, _ = MenuRepository.search_menu(
            db=db,
            kitchen_id=staff_ctx.kitchen_id,
            category_id=category_id,
            search=search,
            is_available=is_available,
            limit=100,
        )

        out = []
        for itm in items:
            has_rec = len(itm.menu_item_ingredients) > 0
            out.append(
                KitchenMenuItemOut(
                    menu_item_id=itm.menu_item_id,
                    kitchen_id=itm.kitchen_id,
                    category_id=itm.category_id,
                    category_name=itm.category.name if itm.category else "General",
                    name=itm.name,
                    description=itm.description,
                    base_price=itm.base_price,
                    is_vegetarian=itm.is_vegetarian,
                    is_available=itm.is_available,
                    preparation_time_minutes=itm.preparation_time_minutes,
                    calories=itm.calories,
                    has_recipe=has_rec,
                    created_at=itm.created_at,
                    updated_at=itm.updated_at,
                )
            )
        return out

    @staticmethod
    def create_menu_item(
        db: Session, staff_ctx: StaffContext, data: KitchenMenuItemCreate
    ) -> KitchenMenuItemOut:
        # Verify category exists
        cat = CategoryRepository.get_by_id(db, data.category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category ID {data.category_id} does not exist",
            )

        # Check unique constraint within kitchen
        existing = (
            db.query(MenuItem)
            .filter(MenuItem.kitchen_id == staff_ctx.kitchen_id, MenuItem.name == data.name.strip())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An item named '{data.name}' already exists in your kitchen's menu",
            )

        item = MenuRepository.create_item(
            db=db,
            kitchen_id=staff_ctx.kitchen_id,
            category_id=data.category_id,
            name=data.name,
            description=data.description,
            base_price=data.base_price,
            is_vegetarian=data.is_vegetarian,
            is_available=data.is_available,
            preparation_time_minutes=data.preparation_time_minutes,
            calories=data.calories,
        )
        db.commit()
        db.refresh(item)

        # Invalidate Redis menu cache
        redis_client.delete(f"menu:kitchen:{staff_ctx.kitchen_id}")
        redis_client.delete("popular:menu_items")

        return KitchenMenuItemOut(
            menu_item_id=item.menu_item_id,
            kitchen_id=item.kitchen_id,
            category_id=item.category_id,
            category_name=cat.name if cat else "General",
            name=item.name,
            description=item.description,
            base_price=item.base_price,
            is_vegetarian=item.is_vegetarian,
            is_available=item.is_available,
            preparation_time_minutes=item.preparation_time_minutes,
            calories=item.calories,
            has_recipe=False,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def update_menu_item(
        db: Session, staff_ctx: StaffContext, item_id: int, data: KitchenMenuItemUpdate
    ) -> KitchenMenuItemOut:
        item = MenuRepository.get_by_id_and_kitchen(db, item_id, staff_ctx.kitchen_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item #{item_id} not found in your kitchen",
            )

        if data.category_id:
            cat = CategoryRepository.get_by_id(db, data.category_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category ID {data.category_id} does not exist",
                )

        if data.name and data.name.strip().lower() != item.name.lower():
            dup = (
                db.query(MenuItem)
                .filter(
                    MenuItem.kitchen_id == staff_ctx.kitchen_id,
                    MenuItem.name == data.name.strip(),
                    MenuItem.menu_item_id != item_id,
                )
                .first()
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An item named '{data.name}' already exists in your kitchen",
                )

        updated = MenuRepository.update_item(
            db=db,
            item=item,
            name=data.name,
            category_id=data.category_id,
            description=data.description,
            base_price=data.base_price,
            is_vegetarian=data.is_vegetarian,
            is_available=data.is_available,
            preparation_time_minutes=data.preparation_time_minutes,
            calories=data.calories,
        )
        db.commit()
        db.refresh(updated)

        cat_name = (
            updated.category.name
            if updated.category
            else (db.query(Category.name).filter(Category.category_id == updated.category_id).scalar() or "General")
        )

        # Invalidate Redis menu cache
        redis_client.delete(f"menu:kitchen:{staff_ctx.kitchen_id}")
        redis_client.delete("popular:menu_items")

        return KitchenMenuItemOut(
            menu_item_id=updated.menu_item_id,
            kitchen_id=updated.kitchen_id,
            category_id=updated.category_id,
            category_name=cat_name,
            name=updated.name,
            description=updated.description,
            base_price=updated.base_price,
            is_vegetarian=updated.is_vegetarian,
            is_available=updated.is_available,
            preparation_time_minutes=updated.preparation_time_minutes,
            calories=updated.calories,
            has_recipe=len(updated.menu_item_ingredients) > 0,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    @staticmethod
    def update_menu_item_availability(
        db: Session, staff_ctx: StaffContext, item_id: int, is_available: bool
    ) -> KitchenMenuItemOut:
        item = MenuRepository.get_by_id_and_kitchen(db, item_id, staff_ctx.kitchen_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item #{item_id} not found in your kitchen",
            )

        updated = MenuRepository.update_availability(db, item, is_available)
        db.commit()
        db.refresh(updated)

        cat_name = (
            updated.category.name
            if updated.category
            else (db.query(Category.name).filter(Category.category_id == updated.category_id).scalar() or "General")
        )

        # Invalidate Redis menu cache
        redis_client.delete(f"menu:kitchen:{staff_ctx.kitchen_id}")
        redis_client.delete("popular:menu_items")

        return KitchenMenuItemOut(
            menu_item_id=updated.menu_item_id,
            kitchen_id=updated.kitchen_id,
            category_id=updated.category_id,
            category_name=cat_name,
            name=updated.name,
            description=updated.description,
            base_price=updated.base_price,
            is_vegetarian=updated.is_vegetarian,
            is_available=updated.is_available,
            preparation_time_minutes=updated.preparation_time_minutes,
            calories=updated.calories,
            has_recipe=len(updated.menu_item_ingredients) > 0,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    # -----------------------------------------------------
    # Kitchen Availability / Operating Status
    # -----------------------------------------------------
    @staticmethod
    def get_availability(db: Session, staff_ctx: StaffContext) -> KitchenAvailabilityOut:
        cache_key = f"kitchen:{staff_ctx.kitchen_id}:availability"
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return KitchenAvailabilityOut(**data)
            except Exception:
                pass

        kitchen = KitchenRepository.get_by_id(db, staff_ctx.kitchen_id)
        if not kitchen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kitchen facility not found",
            )

        is_open = kitchen.operating_status == OperatingStatus.ACTIVE

        res = KitchenAvailabilityOut(
            kitchen_id=kitchen.kitchen_id,
            name=kitchen.name,
            branch_code=kitchen.branch_code,
            operating_status=kitchen.operating_status,
            opening_time=str(kitchen.opening_time),
            closing_time=str(kitchen.closing_time),
            max_active_orders=kitchen.max_active_orders,
            is_open=is_open,
        )

        try:
            redis_client.set(cache_key, json.dumps(res.model_dump(mode="json")), ex=60)
        except Exception:
            pass

        return res

    @staticmethod
    def update_availability(
        db: Session, staff_ctx: StaffContext, data: KitchenAvailabilityUpdate
    ) -> KitchenAvailabilityOut:
        kitchen = KitchenRepository.get_by_id(db, staff_ctx.kitchen_id)
        if not kitchen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kitchen facility not found",
            )

        updated = KitchenRepository.update_operating_status(
            db=db,
            kitchen=kitchen,
            operating_status=data.operating_status,
            max_active_orders=data.max_active_orders,
        )
        db.commit()
        db.refresh(updated)

        # Invalidate Redis cache
        redis_client.delete(f"kitchen:{staff_ctx.kitchen_id}:availability")

        return KitchenService.get_availability(db, staff_ctx)


class MenuService:
    @staticmethod
    def list_categories(db: Session) -> List[CategoryResponse]:
        categories = CategoryRepository.get_all_active(db)
        return [CategoryResponse.model_validate(c) for c in categories]

    @staticmethod
    def search_menu(
        db: Session,
        kitchen_id: Optional[int] = None,
        category_id: Optional[int] = None,
        cuisine_id: Optional[int] = None,
        search: Optional[str] = None,
        is_vegetarian: Optional[bool] = None,
        is_available: Optional[bool] = True,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        # Cache-Aside: check Redis for kitchen catalog or popular items
        cache_key = None
        if kitchen_id and not category_id and not cuisine_id and not search and is_vegetarian is None and sort_by is None and page == 1 and page_size == 20:
            cache_key = f"menu:kitchen:{kitchen_id}"
        elif not kitchen_id and not category_id and not cuisine_id and not search and is_vegetarian is None and sort_by is None and page == 1 and page_size <= 10:
            cache_key = "popular:menu_items"

        if cache_key:
            try:
                cached = redis_client.get_json(cache_key)
                if cached and isinstance(cached, dict) and "items" in cached:
                    return cached
            except Exception:
                pass

        skip = (page - 1) * page_size
        items, total = MenuRepository.search_menu(
            db=db,
            kitchen_id=kitchen_id,
            category_id=category_id,
            cuisine_id=cuisine_id,
            search=search,
            is_vegetarian=is_vegetarian,
            is_available=is_available,
            sort_by=sort_by,
            skip=skip,
            limit=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        res_items = [MenuItemResponse.model_validate(i) for i in items]
        result = {
            "items": [i.model_dump(mode="json") for i in res_items],
            "meta": {
                "total_count": total,
                "page": page,
                "page_size": page_size,
                "total_records": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        if cache_key:
            try:
                redis_client.set_json(cache_key, result, ttl_seconds=600)
            except Exception:
                pass

        return {
            "items": res_items,
            "meta": result["meta"],
        }

    @staticmethod
    def get_menu_detail(db: Session, item_id: int) -> MenuItemDetailResponse:
        item = MenuRepository.get_by_id(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Menu dish not found")
        resp = MenuItemDetailResponse.model_validate(item)
        resp.kitchen_name = item.kitchen.name if item.kitchen else None
        resp.category_name = item.category.name if item.category else None
        resp.cuisine_name = item.cuisine.cuisine_name if item.cuisine else None
        resp.ingredients = [r.ingredient.name for r in item.menu_item_ingredients if r.ingredient]
        return resp

