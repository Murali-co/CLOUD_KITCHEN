import random
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.db.redis import redis_client
from app.models.fulfillment import Coupon, Delivery, DeliveryStatus
from app.models.kitchen import Category, Kitchen, MenuItem, OperatingStatus
from app.models.order import Order, OrderItem, OrderStatus, OrderStatusHistory, Payment, PaymentMethod, PaymentStatus
from app.models.user import Customer, DeliveryPerson, ShiftTiming, Staff, StaffRole, User, UserRole
from app.repositories.admin_repo import AdminRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.admin import (
    AdminAnalyticsOverview,
    AdminAuditLogOut,
    AdminCategoryCreate,
    AdminCategoryOut,
    AdminCategoryUpdate,
    AdminCouponCreate,
    AdminCouponOut,
    AdminCouponUpdate,
    AdminDashboardStats,
    AdminKitchenCreate,
    AdminKitchenOut,
    AdminKitchenStatusUpdate,
    AdminKitchenUpdate,
    AdminMenuItemOut,
    AdminMenuItemStatusUpdate,
    AdminOrderDetailOut,
    AdminOrderItemDetail,
    AdminOrderListItem,
    AdminPaymentOut,
    AdminStaffCreate,
    AdminStaffOut,
    AdminStaffReassign,
    AdminUserOut,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
)


class AdminService:
    # -----------------------------------------------------
    # Dashboard & Overview
    # -----------------------------------------------------
    @staticmethod
    def get_dashboard_metrics(db: Session) -> AdminDashboardStats:
        cache_key = "admin:dashboard:metrics"
        try:
            cached = redis_client.get_json(cache_key)
            if cached:
                return AdminDashboardStats(**cached)
        except Exception:
            pass

        stats = AdminRepository.get_dashboard_stats(db)
        out = AdminDashboardStats(**stats)

        try:
            redis_client.set_json(cache_key, out.model_dump(mode="json"), ex=60)
        except Exception:
            pass

        return out

    # -----------------------------------------------------
    # User Management
    # -----------------------------------------------------
    @staticmethod
    def list_users(
        db: Session,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AdminUserOut], int]:
        users, total = AdminRepository.get_users(
            db=db, search=search, role=role, is_active=is_active, skip=skip, limit=limit
        )

        out = []
        for u in users:
            k_name = u.staff.kitchen.name if (u.staff and u.staff.kitchen) else None
            v_num = u.delivery_person.vehicle_number if u.delivery_person else None
            out.append(
                AdminUserOut(
                    user_id=u.user_id,
                    email=u.email,
                    phone=u.phone_number,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    role=u.role,
                    is_active=u.is_active,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                    kitchen_name=k_name,
                    vehicle_number=v_num,
                )
            )
        return out, total

    @staticmethod
    def get_user_detail(db: Session, user_id: int) -> AdminUserOut:
        u = AdminRepository.get_user_by_id(db, user_id)
        if not u:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found",
            )
        k_name = u.staff.kitchen.name if (u.staff and u.staff.kitchen) else None
        v_num = u.delivery_person.vehicle_number if u.delivery_person else None
        return AdminUserOut(
            user_id=u.user_id,
            email=u.email,
            phone=u.phone_number,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at,
            kitchen_name=k_name,
            vehicle_number=v_num,
        )

    get_user = get_user_detail

    @staticmethod
    def update_user_status(
        db: Session, user_id: int, data: AdminUserStatusUpdate, admin_user_id: int
    ) -> AdminUserOut:
        user = AdminRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found",
            )

        # Protection: Prevent deactivation of the last active administrator
        if user.role == UserRole.ADMIN and data.is_active is False:
            active_admin_count = AdminRepository.count_active_admins(db)
            if active_admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Operation rejected: Cannot deactivate the platform's last active administrator.",
                )

        old_status = user.is_active
        user.is_active = data.is_active

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_USER_STATUS",
            entity_type="USER",
            entity_id=user_id,
            details={
                "previous_is_active": old_status,
                "new_is_active": data.is_active,
                "reason": data.reason,
                "user_email": user.email,
            },
        )

        db.commit()
        db.refresh(user)
        return AdminService.get_user_detail(db, user_id)

    @staticmethod
    def update_user_role(
        db: Session, user_id: int, data: AdminUserRoleUpdate, admin_user_id: int
    ) -> AdminUserOut:
        user = AdminRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {user_id} not found",
            )

        # Protection: Prevent demoting the last active administrator
        if user.role == UserRole.ADMIN and data.role != UserRole.ADMIN:
            active_admin_count = AdminRepository.count_active_admins(db)
            if active_admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Operation rejected: Cannot demote the platform's last active administrator.",
                )

        old_role = user.role
        user.role = data.role

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_USER_ROLE",
            entity_type="USER",
            entity_id=user_id,
            details={
                "previous_role": old_role.value,
                "new_role": data.role.value,
                "reason": data.reason,
                "user_email": user.email,
            },
        )

        db.commit()
        db.refresh(user)
        return AdminService.get_user_detail(db, user_id)

    # -----------------------------------------------------
    # Kitchen & Staff Management
    # -----------------------------------------------------
    @staticmethod
    def list_kitchens(db: Session, skip: int = 0, limit: int = 50) -> Tuple[List[AdminKitchenOut], int]:
        kitchens, total = AdminRepository.get_kitchens(db, skip=skip, limit=limit)
        out = []
        for k in kitchens:
            staff_count = len(k.staff_members) if k.staff_members else 0
            items_count = len(k.menu_items) if k.menu_items else 0
            out.append(
                AdminKitchenOut(
                    kitchen_id=k.kitchen_id,
                    name=k.name,
                    street_address=k.address_line1,
                    city=k.city,
                    state=k.state,
                    postal_code=k.postal_code,
                    phone=k.contact_phone,
                    email=k.email,
                    operating_status=k.operating_status,
                    is_active=(k.operating_status == OperatingStatus.ACTIVE),
                    max_orders_per_hour=k.max_active_orders,
                    active_staff_count=staff_count,
                    menu_items_count=items_count,
                    created_at=k.created_at,
                )
            )
        return out, total

    @staticmethod
    def get_kitchen_detail(db: Session, kitchen_id: int) -> AdminKitchenOut:
        k = AdminRepository.get_kitchen_by_id(db, kitchen_id)
        if not k:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kitchen ID {kitchen_id} not found",
            )
        staff_count = len(k.staff_members) if k.staff_members else 0
        items_count = len(k.menu_items) if k.menu_items else 0
        return AdminKitchenOut(
            kitchen_id=k.kitchen_id,
            name=k.name,
            street_address=k.address_line1,
            city=k.city,
            state=k.state,
            postal_code=k.postal_code,
            phone=k.contact_phone,
            email=k.email,
            operating_status=k.operating_status,
            is_active=(k.operating_status == OperatingStatus.ACTIVE),
            max_orders_per_hour=k.max_active_orders,
            active_staff_count=staff_count,
            menu_items_count=items_count,
            created_at=k.created_at,
        )

    @staticmethod
    def create_kitchen(db: Session, data: AdminKitchenCreate, admin_user_id: int) -> AdminKitchenOut:
        # Check duplicate name
        existing = db.query(Kitchen).filter(Kitchen.name == data.name.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kitchen with name '{data.name}' already exists",
            )

        branch_code = f"CK-{data.city[:3].upper()}-{data.name[:3].upper()}-{random.randint(10, 99)}"
        kitchen_data = {
            "name": data.name.strip(),
            "branch_code": branch_code,
            "address_line1": data.street_address.strip(),
            "city": data.city.strip(),
            "state": data.state.strip(),
            "postal_code": data.postal_code.strip(),
            "contact_phone": data.phone.strip(),
            "email": data.email.strip(),
            "max_active_orders": data.max_orders_per_hour,
            "operating_status": OperatingStatus.ACTIVE,
        }
        k = AdminRepository.create_kitchen(db, kitchen_data)
        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="CREATE_KITCHEN",
            entity_type="KITCHEN",
            entity_id=k.kitchen_id,
            details={"name": k.name, "city": k.city},
        )
        db.commit()
        db.refresh(k)
        return AdminService.get_kitchen_detail(db, k.kitchen_id)

    @staticmethod
    def update_kitchen(
        db: Session, kitchen_id: int, data: AdminKitchenUpdate, admin_user_id: int
    ) -> AdminKitchenOut:
        k = db.query(Kitchen).filter(Kitchen.kitchen_id == kitchen_id).first()
        if not k:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kitchen ID {kitchen_id} not found",
            )

        if data.name:
            k.name = data.name.strip()
        if data.street_address:
            k.address_line1 = data.street_address.strip()
        if data.city:
            k.city = data.city.strip()
        if data.state:
            k.state = data.state.strip()
        if data.postal_code:
            k.postal_code = data.postal_code.strip()
        if data.phone:
            k.contact_phone = data.phone.strip()
        if data.email:
            k.email = data.email.strip()
        if data.max_orders_per_hour:
            k.max_active_orders = data.max_orders_per_hour

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_KITCHEN",
            entity_type="KITCHEN",
            entity_id=kitchen_id,
            details=data.model_dump(exclude_unset=True),
        )
        db.commit()
        db.refresh(k)
        return AdminService.get_kitchen_detail(db, kitchen_id)

    @staticmethod
    def update_kitchen_status(
        db: Session, kitchen_id: int, data: AdminKitchenStatusUpdate, admin_user_id: int
    ) -> AdminKitchenOut:
        k = db.query(Kitchen).filter(Kitchen.kitchen_id == kitchen_id).first()
        if not k:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kitchen ID {kitchen_id} not found",
            )

        # Soft deactivation preserves all historical orders
        if data.operating_status is not None:
            k.operating_status = data.operating_status
        elif data.is_active is not None:
            k.operating_status = OperatingStatus.ACTIVE if data.is_active else OperatingStatus.INACTIVE

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_KITCHEN_STATUS",
            entity_type="KITCHEN",
            entity_id=kitchen_id,
            details={"operating_status": k.operating_status.value, "reason": data.reason},
        )
        db.commit()
        db.refresh(k)
        return AdminService.get_kitchen_detail(db, kitchen_id)

    @staticmethod
    def list_staff(
        db: Session, kitchen_id: Optional[int] = None, skip: int = 0, limit: int = 50
    ) -> Tuple[List[AdminStaffOut], int]:
        staff_members, total = AdminRepository.get_staff_list(db, kitchen_id=kitchen_id, skip=skip, limit=limit)
        out = []
        for s in staff_members:
            user = s.user
            out.append(
                AdminStaffOut(
                    staff_id=s.staff_id,
                    user_id=user.user_id,
                    full_name=f"{user.first_name} {user.last_name}",
                    email=user.email,
                    phone=user.phone_number,
                    kitchen_id=s.kitchen_id,
                    kitchen_name=s.kitchen.name if s.kitchen else "Unknown",
                    staff_role=s.staff_role,
                    shift_timing=s.shift_timing,
                    hired_date=s.hired_date,
                    is_active=user.is_active,
                )
            )
        return out, total

    @staticmethod
    def create_staff(db: Session, data: AdminStaffCreate, admin_user_id: int) -> AdminStaffOut:
        # Check kitchen exists
        k = db.query(Kitchen).filter(Kitchen.kitchen_id == data.kitchen_id).first()
        if not k:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kitchen ID {data.kitchen_id} does not exist",
            )

        # Check email uniqueness
        existing_user = db.query(User).filter(User.email == data.email.lower().strip()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Account with email '{data.email}' already exists",
            )

        new_user = User(
            email=data.email.lower().strip(),
            password_hash=hash_password(data.password),
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            phone_number=data.phone.strip(),
            role=UserRole.KITCHEN_STAFF,
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        staff_entry = Staff(
            staff_id=new_user.user_id,
            kitchen_id=data.kitchen_id,
            staff_role=data.staff_role,
            shift_timing=data.shift_timing,
            hired_date=date.today(),
        )
        db.add(staff_entry)
        db.flush()

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="CREATE_STAFF_ACCOUNT",
            entity_type="STAFF",
            entity_id=staff_entry.staff_id,
            details={
                "staff_email": new_user.email,
                "kitchen_id": data.kitchen_id,
                "kitchen_name": k.name,
                "staff_role": data.staff_role.value,
            },
        )
        db.commit()
        db.refresh(staff_entry)

        return AdminStaffOut(
            staff_id=staff_entry.staff_id,
            user_id=new_user.user_id,
            full_name=f"{new_user.first_name} {new_user.last_name}",
            email=new_user.email,
            phone=new_user.phone_number,
            kitchen_id=k.kitchen_id,
            kitchen_name=k.name,
            staff_role=staff_entry.staff_role,
            shift_timing=staff_entry.shift_timing,
            hired_date=staff_entry.hired_date,
            is_active=new_user.is_active,
        )

    @staticmethod
    def reassign_staff(
        db: Session, staff_id: int, data: AdminStaffReassign, admin_user_id: int
    ) -> AdminStaffOut:
        s = db.query(Staff).options(joinedload(Staff.user), joinedload(Staff.kitchen)).filter(Staff.staff_id == staff_id).first()
        if not s:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Staff ID {staff_id} not found",
            )

        old_kitchen = s.kitchen_id
        old_role = s.staff_role

        if data.kitchen_id is not None:
            k = db.query(Kitchen).filter(Kitchen.kitchen_id == data.kitchen_id).first()
            if not k:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target kitchen ID {data.kitchen_id} does not exist",
                )
            s.kitchen_id = data.kitchen_id

        if data.staff_role is not None:
            s.staff_role = data.staff_role
        if data.shift_timing is not None:
            s.shift_timing = data.shift_timing

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="REASSIGN_STAFF",
            entity_type="STAFF",
            entity_id=staff_id,
            details={
                "previous_kitchen_id": old_kitchen,
                "new_kitchen_id": s.kitchen_id,
                "previous_role": old_role.value,
                "new_role": s.staff_role.value,
            },
        )
        db.commit()
        db.refresh(s)

        user = s.user
        return AdminStaffOut(
            staff_id=s.staff_id,
            user_id=user.user_id,
            full_name=f"{user.first_name} {user.last_name}",
            email=user.email,
            phone=user.phone_number,
            kitchen_id=s.kitchen_id,
            kitchen_name=s.kitchen.name if s.kitchen else "Kitchen",
            staff_role=s.staff_role,
            shift_timing=s.shift_timing,
            hired_date=s.hired_date,
            is_active=user.is_active,
        )

    # -----------------------------------------------------
    # Menu and Categories
    # -----------------------------------------------------
    @staticmethod
    def list_menu_items(
        db: Session,
        kitchen_id: Optional[int] = None,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AdminMenuItemOut], int]:
        query = db.query(MenuItem).options(joinedload(MenuItem.kitchen), joinedload(MenuItem.category))

        if kitchen_id:
            query = query.filter(MenuItem.kitchen_id == kitchen_id)
        if category_id:
            query = query.filter(MenuItem.category_id == category_id)
        if is_active is not None:
            query = query.filter(MenuItem.is_available == is_active)
        if search:
            query = query.filter(MenuItem.name.ilike(f"%{search}%"))

        total = query.count()
        items = query.order_by(MenuItem.menu_item_id).offset(skip).limit(limit).all()

        out = []
        for itm in items:
            out.append(
                AdminMenuItemOut(
                    menu_item_id=itm.menu_item_id,
                    kitchen_id=itm.kitchen_id,
                    kitchen_name=itm.kitchen.name if itm.kitchen else "Kitchen",
                    category_id=itm.category_id,
                    category_name=itm.category.name if itm.category else "Category",
                    name=itm.name,
                    description=itm.description,
                    base_price=itm.base_price,
                    is_vegetarian=itm.is_vegetarian,
                    is_available=itm.is_available,
                    is_active=itm.is_available,
                    preparation_time_minutes=itm.preparation_time_minutes,
                    calories=itm.calories,
                    created_at=itm.created_at,
                )
            )
        return out, total

    @staticmethod
    def update_menu_item_status(
        db: Session, item_id: int, data: AdminMenuItemStatusUpdate, admin_user_id: int
    ) -> AdminMenuItemOut:
        itm = db.query(MenuItem).options(joinedload(MenuItem.kitchen), joinedload(MenuItem.category)).filter(MenuItem.menu_item_id == item_id).first()
        if not itm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item ID {item_id} not found",
            )

        target_val = data.is_available if data.is_available is not None else data.is_active
        if target_val is not None:
            itm.is_available = target_val

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_MENU_ITEM_STATUS",
            entity_type="MENU_ITEM",
            entity_id=item_id,
            details={"name": itm.name, "is_available": itm.is_available},
        )
        db.commit()
        db.refresh(itm)

        # Invalidate kitchen menu cache
        try:
            redis_client.delete(f"menu:kitchen:{itm.kitchen_id}")
            redis_client.delete("popular:menu_items")
        except Exception:
            pass

        return AdminMenuItemOut(
            menu_item_id=itm.menu_item_id,
            kitchen_id=itm.kitchen_id,
            kitchen_name=itm.kitchen.name if itm.kitchen else "Kitchen",
            category_id=itm.category_id,
            category_name=itm.category.name if itm.category else "Category",
            name=itm.name,
            description=itm.description,
            base_price=itm.base_price,
            is_vegetarian=itm.is_vegetarian,
            is_available=itm.is_available,
            is_active=itm.is_available,
            preparation_time_minutes=itm.preparation_time_minutes,
            calories=itm.calories,
            created_at=itm.created_at,
        )

    @staticmethod
    def list_categories(db: Session) -> List[AdminCategoryOut]:
        cats = db.query(Category).order_by(Category.category_id).all()
        return [
            AdminCategoryOut(
                category_id=c.category_id,
                name=c.name,
                description=c.description,
                image_url=c.image_url,
                created_at=c.created_at,
            )
            for c in cats
        ]

    @staticmethod
    def create_category(db: Session, data: AdminCategoryCreate, admin_user_id: int) -> AdminCategoryOut:
        existing = db.query(Category).filter(Category.name == data.name.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{data.name}' already exists",
            )
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", data.name.strip().lower()).strip("-")
        cat = Category(
            name=data.name.strip(),
            slug=slug,
            description=data.description.strip() if data.description else None,
        )
        db.add(cat)
        db.flush()

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="CREATE_CATEGORY",
            entity_type="CATEGORY",
            entity_id=cat.category_id,
            details={"name": cat.name, "slug": slug},
        )
        db.commit()
        db.refresh(cat)
        return AdminCategoryOut(
            category_id=cat.category_id,
            name=cat.name,
            description=cat.description,
            image_url=None,
            created_at=cat.created_at,
        )

    @staticmethod
    def update_category(
        db: Session, category_id: int, data: AdminCategoryUpdate, admin_user_id: int
    ) -> AdminCategoryOut:
        cat = db.query(Category).filter(Category.category_id == category_id).first()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category ID {category_id} not found",
            )
        if data.name:
            cat.name = data.name.strip()
            cat.slug = re.sub(r"[^a-zA-Z0-9]+", "-", data.name.strip().lower()).strip("-")
        if data.description is not None:
            cat.description = data.description.strip() if data.description else None

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_CATEGORY",
            entity_type="CATEGORY",
            entity_id=category_id,
            details={"name": cat.name},
        )
        db.commit()
        db.refresh(cat)
        return AdminCategoryOut(
            category_id=cat.category_id,
            name=cat.name,
            description=cat.description,
            image_url=None,
            created_at=cat.created_at,
        )

    # -----------------------------------------------------
    # Order Administration
    # -----------------------------------------------------
    @staticmethod
    def list_orders(
        db: Session,
        search: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        status_filter: Optional[OrderStatus] = None,
        kitchen_id: Optional[int] = None,
        date_from: Optional[Any] = None,
        start_date: Optional[Any] = None,
        date_to: Optional[Any] = None,
        end_date: Optional[Any] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AdminOrderListItem], int]:
        target_status = status_filter if status_filter is not None else status
        d_from = start_date if start_date is not None else date_from
        d_to = end_date if end_date is not None else date_to
        if d_from and isinstance(d_from, date) and not isinstance(d_from, datetime):
            d_from = datetime.combine(d_from, datetime.min.time())
        if d_to and isinstance(d_to, date) and not isinstance(d_to, datetime):
            d_to = datetime.combine(d_to, datetime.max.time())

        orders, total = AdminRepository.get_orders(
            db=db,
            search=search,
            status=target_status,
            kitchen_id=kitchen_id,
            date_from=d_from,
            date_to=d_to,
            skip=skip,
            limit=limit,
        )

        out = []
        for o in orders:
            cust_user = o.customer.user if (o.customer and hasattr(o.customer, "user") and o.customer.user) else None
            c_name = f"{cust_user.first_name} {cust_user.last_name}" if cust_user else "Customer"
            del_driver = o.delivery.delivery_person if o.delivery else None
            del_name = f"{del_driver.user.first_name} {del_driver.user.last_name}" if (del_driver and del_driver.user) else None
            pay = o.payments[0] if (hasattr(o, "payments") and o.payments) else None

            out.append(
                AdminOrderListItem(
                    order_id=o.order_id,
                    order_number=o.order_number,
                    kitchen_id=o.kitchen_id,
                    kitchen_name=o.kitchen.name if o.kitchen else "Kitchen",
                    customer_id=o.customer_id,
                    customer_name=c_name,
                    order_status=o.order_status,
                    payment_status=pay.payment_status if pay else PaymentStatus.PENDING,
                    payment_method=pay.payment_method if pay else PaymentMethod.UPI,
                    delivery_status=o.delivery.delivery_status if o.delivery else None,
                    delivery_person_name=del_name,
                    total_amount=o.total_amount,
                    item_count=len(o.order_items) if o.order_items else 0,
                    created_at=o.placed_at,
                )
            )
        return out, total

    @staticmethod
    def get_order_detail(db: Session, order_id: int) -> AdminOrderDetailOut:
        o = AdminRepository.get_order_by_id(db, order_id)
        if not o:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order ID {order_id} not found",
            )

        cust_user = o.customer.user if (o.customer and hasattr(o.customer, "user") and o.customer.user) else None
        c_name = f"{cust_user.first_name} {cust_user.last_name}" if cust_user else "Customer"
        c_phone = cust_user.phone_number if cust_user else None
        c_email = cust_user.email if cust_user else "unknown"

        addr = None
        if o.delivery_address:
            addr = f"{o.delivery_address.address_line1}, {o.delivery_address.city} - {o.delivery_address.postal_code}"

        del_info = None
        if o.delivery:
            driver = o.delivery.delivery_person
            d_name = f"{driver.user.first_name} {driver.user.last_name}" if (driver and driver.user) else None
            del_info = {
                "delivery_id": o.delivery.delivery_id,
                "delivery_person_id": o.delivery.delivery_person_id,
                "delivery_person_name": d_name,
                "delivery_status": o.delivery.delivery_status.value,
                "assigned_at": o.delivery.assigned_at.isoformat() if o.delivery.assigned_at else None,
                "picked_up_at": o.delivery.picked_up_at.isoformat() if o.delivery.picked_up_at else None,
                "delivered_at": o.delivery.delivered_at.isoformat() if o.delivery.delivered_at else None,
                "delivery_otp": o.delivery.delivery_otp,
            }

        items = [
            AdminOrderItemDetail(
                item_name=itm.item_name_snapshot,
                quantity=itm.quantity,
                unit_price=itm.unit_price_snapshot,
                subtotal=itm.subtotal_price,
            )
            for itm in (o.order_items or [])
        ]

        history = [
            {
                "previous_status": h.previous_status.value if h.previous_status else None,
                "new_status": h.new_status.value,
                "changed_by_user_id": h.changed_by_user_id,
                "notes": h.notes,
                "created_at": h.created_at.isoformat(),
            }
            for h in (o.status_history or [])
        ]

        pay = o.payments[0] if (hasattr(o, "payments") and o.payments) else None

        return AdminOrderDetailOut(
            order_id=o.order_id,
            order_number=o.order_number,
            kitchen_id=o.kitchen_id,
            kitchen_name=o.kitchen.name if o.kitchen else "Kitchen",
            customer_name=c_name,
            customer_phone=c_phone,
            customer_email=c_email,
            delivery_address=addr,
            order_status=o.order_status,
            payment_status=pay.payment_status if pay else PaymentStatus.PENDING,
            payment_method=pay.payment_method if pay else PaymentMethod.UPI,
            subtotal=o.subtotal_amount,
            tax_amount=o.tax_amount,
            delivery_fee=o.delivery_fee,
            discount_amount=o.discount_amount,
            total_amount=o.total_amount,
            items=items,
            delivery=del_info,
            status_history=history,
            created_at=o.placed_at,
        )

    get_order = get_order_detail

    @staticmethod
    def cancel_order(db: Session, order_id: int, reason: str, admin_user_id: int) -> AdminOrderDetailOut:
        o = AdminRepository.get_order_by_id(db, order_id)
        if not o:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order ID {order_id} not found",
            )

        if o.order_status == OrderStatus.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel an order that has already been marked DELIVERED",
            )
        if o.order_status == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is already cancelled",
            )

        old_status = o.order_status
        o.order_status = OrderStatus.CANCELLED

        # If delivery was active, update delivery to FAILED
        if o.delivery and o.delivery.delivery_status in [DeliveryStatus.ASSIGNED, DeliveryStatus.PICKED_UP, DeliveryStatus.OUT_FOR_DELIVERY]:
            o.delivery.delivery_status = DeliveryStatus.FAILED
            o.delivery.delivery_notes = f"Admin Cancelled: {reason}"
            if o.delivery.delivery_person:
                o.delivery.delivery_person.current_status = DeliveryPersonStatus.AVAILABLE

        hist = OrderStatusHistory(
            order_id=order_id,
            changed_by_user_id=admin_user_id,
            previous_status=old_status,
            new_status=OrderStatus.CANCELLED,
            notes=f"Administrator cancellation: {reason}",
        )
        db.add(hist)

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="ADMIN_CANCEL_ORDER",
            entity_type="ORDER",
            entity_id=order_id,
            details={"previous_status": old_status.value, "reason": reason},
        )

        db.commit()
        db.refresh(o)

        try:
            redis_client.delete(f"order:tracking:{order_id}")
            redis_client.delete("admin:dashboard:metrics")
        except Exception:
            pass

        return AdminService.get_order_detail(db, order_id)

    cancel_order_admin = cancel_order

    # -----------------------------------------------------
    # Payments
    # -----------------------------------------------------
    @staticmethod
    def list_payments(
        db: Session,
        search: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        status_filter: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None,
        date_from: Optional[Any] = None,
        start_date: Optional[Any] = None,
        date_to: Optional[Any] = None,
        end_date: Optional[Any] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AdminPaymentOut], int]:
        target_status = status_filter if status_filter is not None else status
        d_from = start_date if start_date is not None else date_from
        d_to = end_date if end_date is not None else date_to
        if d_from and isinstance(d_from, date) and not isinstance(d_from, datetime):
            d_from = datetime.combine(d_from, datetime.min.time())
        if d_to and isinstance(d_to, date) and not isinstance(d_to, datetime):
            d_to = datetime.combine(d_to, datetime.max.time())

        payments, total = AdminRepository.get_payments(
            db=db,
            search=search,
            status=target_status,
            method=method,
            date_from=d_from,
            date_to=d_to,
            skip=skip,
            limit=limit,
        )

        out = []
        for p in payments:
            out.append(
                AdminPaymentOut(
                    payment_id=p.payment_id,
                    order_id=p.order_id,
                    order_number=p.order.order_number if p.order else f"#{p.order_id}",
                    amount=p.amount,
                    currency=p.currency,
                    payment_method=p.payment_method,
                    payment_status=p.payment_status,
                    payment_reference=p.transaction_reference or f"TXN-{p.payment_id}",
                    transaction_reference=p.transaction_reference or f"TXN-{p.payment_id}",
                    created_at=p.initiated_at,
                )
            )
        return out, total

    # -----------------------------------------------------
    # Coupons
    # -----------------------------------------------------
    @staticmethod
    def list_coupons(db: Session, active_only: bool = False, skip: int = 0, limit: int = 50) -> Tuple[List[AdminCouponOut], int]:
        coupons, total = AdminRepository.get_coupons(db, skip=skip, limit=limit)
        out = []
        for c in coupons:
            out.append(
                AdminCouponOut(
                    coupon_id=c.coupon_id,
                    code=c.code,
                    description=c.description,
                    discount_type=c.discount_type,
                    discount_value=c.discount_value,
                    min_order_value=c.min_order_value,
                    max_discount_amount=c.max_discount_amount,
                    valid_from=c.valid_from,
                    valid_to=c.valid_to,
                    usage_limit_per_user=c.usage_limit_per_user,
                    total_usage_limit=c.total_usage_limit,
                    current_usage_count=c.current_usage_count,
                    is_active=c.is_active,
                    created_at=c.created_at,
                )
            )
        return out, total

    @staticmethod
    def create_coupon(db: Session, data: AdminCouponCreate, admin_user_id: int) -> AdminCouponOut:
        existing = db.query(Coupon).filter(Coupon.code == data.code.upper().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coupon code '{data.code}' already exists",
            )
        coupon_data = data.model_dump()
        coupon_data["code"] = data.code.upper().strip()

        c = AdminRepository.create_coupon(db, coupon_data)
        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="CREATE_COUPON",
            entity_type="COUPON",
            entity_id=c.coupon_id,
            details={"code": c.code, "discount_value": str(c.discount_value)},
        )
        db.commit()
        db.refresh(c)

        return AdminCouponOut(
            coupon_id=c.coupon_id,
            code=c.code,
            description=c.description,
            discount_type=c.discount_type,
            discount_value=c.discount_value,
            min_order_value=c.min_order_value,
            max_discount_amount=c.max_discount_amount,
            valid_from=c.valid_from,
            valid_to=c.valid_to,
            usage_limit_per_user=c.usage_limit_per_user,
            total_usage_limit=c.total_usage_limit,
            current_usage_count=c.current_usage_count,
            is_active=c.is_active,
            created_at=c.created_at,
        )

    @staticmethod
    def update_coupon(
        db: Session, coupon_id: int, data: AdminCouponUpdate, admin_user_id: int
    ) -> AdminCouponOut:
        c = AdminRepository.get_coupon_by_id(db, coupon_id)
        if not c:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coupon ID {coupon_id} not found",
            )

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(c, key, val)

        AuditRepository.record_audit(
            db=db,
            actor_user_id=admin_user_id,
            action="UPDATE_COUPON",
            entity_type="COUPON",
            entity_id=coupon_id,
            details={"code": c.code, "updated_fields": list(update_dict.keys())},
        )
        db.commit()
        db.refresh(c)

        return AdminCouponOut(
            coupon_id=c.coupon_id,
            code=c.code,
            description=c.description,
            discount_type=c.discount_type,
            discount_value=c.discount_value,
            min_order_value=c.min_order_value,
            max_discount_amount=c.max_discount_amount,
            valid_from=c.valid_from,
            valid_to=c.valid_to,
            usage_limit_per_user=c.usage_limit_per_user,
            total_usage_limit=c.total_usage_limit,
            current_usage_count=c.current_usage_count,
            is_active=c.is_active,
            created_at=c.created_at,
        )

    # -----------------------------------------------------
    # Analytics
    # -----------------------------------------------------
    @staticmethod
    def get_analytics(
        db: Session, date_from_str: Optional[str] = None, date_to_str: Optional[str] = None
    ) -> AdminAnalyticsOverview:
        if date_to_str:
            d_to = datetime.strptime(date_to_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        else:
            d_to = datetime.utcnow()

        if date_from_str:
            d_from = datetime.strptime(date_from_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        else:
            d_from = d_to - timedelta(days=30)

        analytics_dict = AdminRepository.get_analytics(db, d_from, d_to)
        return AdminAnalyticsOverview(**analytics_dict)

    @staticmethod
    def get_analytics_overview(db: Session, days: int = 30) -> AdminAnalyticsOverview:
        d_to = datetime.utcnow()
        d_from = d_to - timedelta(days=days)
        analytics_dict = AdminRepository.get_analytics(db, d_from, d_to)
        return AdminAnalyticsOverview(**analytics_dict)

    # -----------------------------------------------------
    # Audit Logs
    # -----------------------------------------------------
    @staticmethod
    def list_audit_logs(
        db: Session,
        actor_user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AdminAuditLogOut], int]:
        logs, total = AuditRepository.get_audit_logs(
            db=db,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            action=action,
            skip=skip,
            limit=limit,
        )

        out = []
        for l in logs:
            actor = l.actor_user
            out.append(
                AdminAuditLogOut(
                    audit_id=l.audit_id,
                    actor_user_id=l.actor_user_id,
                    actor_name=f"{actor.first_name} {actor.last_name}" if actor else "System",
                    actor_email=actor.email if actor else "system@gourmetcloud.com",
                    action=l.action,
                    entity_type=l.entity_type,
                    entity_id=l.entity_id,
                    details=l.details,
                    created_at=l.created_at,
                )
            )
        return out, total
