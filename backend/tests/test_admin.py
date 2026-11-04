import pytest
from datetime import date, datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit import AdminAuditLog
from app.models.kitchen import Kitchen, MenuItem, OperatingStatus
from app.models.order import Order, OrderItem, OrderStatus, Payment, PaymentMethod, PaymentStatus
from app.models.user import User, UserRole


# 14. Admin-only API access & 15. Non-admin rejection
def test_admin_access_control(
    client: TestClient,
    admin_auth_headers: dict,
    customer_auth_headers: dict,
    kitchen_staff_headers: dict,
    delivery_auth_headers: dict,
):
    # 14. Admin can access dashboard
    admin_res = client.get("/api/v1/admin/dashboard", headers=admin_auth_headers)
    assert admin_res.status_code == 200
    assert admin_res.json()["success"] is True

    # 15. Non-admins MUST receive 403 Forbidden
    cust_res = client.get("/api/v1/admin/dashboard", headers=customer_auth_headers)
    assert cust_res.status_code == 403

    kitchen_res = client.get("/api/v1/admin/dashboard", headers=kitchen_staff_headers)
    assert kitchen_res.status_code == 403

    driver_res = client.get("/api/v1/admin/dashboard", headers=delivery_auth_headers)
    assert driver_res.status_code == 403


# 16. User listing, search, and 30. Sensitive info protection
def test_user_listing_and_sensitive_info_protection(client: TestClient, admin_auth_headers: dict):
    # 16. List and search
    res = client.get("/api/v1/admin/users?search=customer1", headers=admin_auth_headers)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) >= 1
    user = items[0]
    assert user["email"] == "customer1@test.com"

    # 30. Sensitive information protection: password_hash MUST NOT be exposed
    assert "password_hash" not in user
    assert "password" not in user

    # Detail endpoint also protects passwords
    detail_res = client.get(f"/api/v1/admin/users/{user['user_id']}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert "password_hash" not in detail


# 17. User activation/deactivation & 18. Role modification & 19. Last administrator protection
def test_user_management_and_last_admin_protection(
    client: TestClient, admin_auth_headers: dict, db_session: Session
):
    # 17. Activate / deactivate customer
    deact_res = client.patch(
        "/api/v1/admin/users/10/status",
        headers=admin_auth_headers,
        json={"is_active": False, "reason": "Suspended for TOS violation"},
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["is_active"] is False

    react_res = client.patch(
        "/api/v1/admin/users/10/status",
        headers=admin_auth_headers,
        json={"is_active": True},
    )
    assert react_res.status_code == 200
    assert react_res.json()["data"]["is_active"] is True

    # 18. Role modification: promote user 20 to KITCHEN_STAFF
    role_res = client.patch(
        "/api/v1/admin/users/20/role",
        headers=admin_auth_headers,
        json={"role": "KITCHEN_STAFF"},
    )
    assert role_res.status_code == 200
    assert role_res.json()["data"]["role"] == "KITCHEN_STAFF"

    # 19. Last administrator protection:
    # User 40 is the ONLY active admin. Attempting to deactivate User 40 MUST fail with 400.
    bad_deact = client.patch(
        "/api/v1/admin/users/40/status",
        headers=admin_auth_headers,
        json={"is_active": False},
    )
    assert bad_deact.status_code == 400
    assert "last active administrator" in bad_deact.json()["detail"]

    # Attempting to demote User 40 to CUSTOMER MUST fail with 400
    bad_demote = client.patch(
        "/api/v1/admin/users/40/role",
        headers=admin_auth_headers,
        json={"role": "CUSTOMER"},
    )
    assert bad_demote.status_code == 400
    assert "last active administrator" in bad_demote.json()["detail"]


# 20. Kitchen creation & 21. Kitchen update
def test_kitchen_crud(client: TestClient, admin_auth_headers: dict):
    # 20. Create kitchen
    create_res = client.post(
        "/api/v1/admin/kitchens",
        headers=admin_auth_headers,
        json={
            "name": "Whitefield Hub",
            "street_address": "ITPL Main Rd",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560066",
            "phone": "+918099887766",
            "email": "whitefield@cloudkitchen.com",
            "max_orders_per_hour": 75,
        },
    )
    assert create_res.status_code == 201
    k_data = create_res.json()["data"]
    assert k_data["name"] == "Whitefield Hub"
    k_id = k_data["kitchen_id"]

    # 21. Update kitchen
    upd_res = client.put(
        f"/api/v1/admin/kitchens/{k_id}",
        headers=admin_auth_headers,
        json={"name": "Whitefield Tech Central", "max_orders_per_hour": 100},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["name"] == "Whitefield Tech Central"

    # Toggle operating status
    status_res = client.patch(
        f"/api/v1/admin/kitchens/{k_id}/status",
        headers=admin_auth_headers,
        json={"operating_status": "MAINTENANCE"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["operating_status"] == "MAINTENANCE"


# 22. Staff assignment
def test_staff_management(client: TestClient, admin_auth_headers: dict):
    # Create staff
    res = client.post(
        "/api/v1/admin/staff",
        headers=admin_auth_headers,
        json={
            "email": "newstaff@test.com",
            "password": "Password@123",
            "first_name": "Deepak",
            "last_name": "Sharma",
            "phone": "+919800000088",
            "kitchen_id": 1,
            "staff_role": "LINE_COOK",
            "shift_timing": "MORNING",
        },
    )
    assert res.status_code == 201
    staff_data = res.json()["data"]
    staff_id = staff_data["staff_id"]
    assert staff_data["kitchen_id"] == 1

    # Reassign staff to Kitchen 2
    reassign_res = client.patch(
        f"/api/v1/admin/staff/{staff_id}/reassign",
        headers=admin_auth_headers,
        json={"kitchen_id": 2, "shift_timing": "NIGHT"},
    )
    assert reassign_res.status_code == 200
    assert reassign_res.json()["data"]["kitchen_id"] == 2


# 23. Menu and Category administration
def test_menu_and_category_administration(client: TestClient, admin_auth_headers: dict):
    # Create category
    cat_res = client.post(
        "/api/v1/admin/categories",
        headers=admin_auth_headers,
        json={"name": "Desserts & Shakes", "description": "Sweet treats"},
    )
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["category_id"]

    # Toggle menu item status
    menu_toggle = client.patch(
        "/api/v1/admin/menu/1/status",
        headers=admin_auth_headers,
        json={"is_available": False},
    )
    assert menu_toggle.status_code == 200
    assert menu_toggle.json()["data"]["is_available"] is False

    menu_toggle_back = client.patch(
        "/api/v1/admin/menu/1/status",
        headers=admin_auth_headers,
        json={"is_available": True},
    )
    assert menu_toggle_back.status_code == 200
    assert menu_toggle_back.json()["data"]["is_available"] is True


# 24. Order listing, filtering & admin cancellation
def test_order_administration(client: TestClient, admin_auth_headers: dict, db_session: Session):
    order = Order(
        customer_id=10,
        kitchen_id=1,
        delivery_address_id=1,
        order_number=f"ORD-ADM-{datetime.utcnow().strftime('%f')}",
        order_status=OrderStatus.PENDING,
        subtotal_amount=Decimal("300.00"),
        tax_amount=Decimal("15.00"),
        delivery_fee=Decimal("40.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("355.00"),
    )
    db_session.add(order)
    db_session.flush()

    pay = Payment(
        order_id=order.order_id,
        payment_method=PaymentMethod.CREDIT_CARD,
        payment_status=PaymentStatus.PENDING,
        amount=Decimal("355.00"),
        transaction_reference=f"TXN-ADM-ORD-{order.order_id}",
    )
    db_session.add(pay)
    db_session.commit()

    # List orders with status filter
    res = client.get("/api/v1/admin/orders?status=PENDING", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["meta"]["total_count"] >= 1

    # Inspect order detail
    detail_res = client.get(f"/api/v1/admin/orders/{order.order_id}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["order_id"] == order.order_id

    # Admin cancellation
    cancel_res = client.post(
        f"/api/v1/admin/orders/{order.order_id}/cancel?reason=Store closed due to emergency",
        headers=admin_auth_headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["order_status"] == "CANCELLED"


# 25. Payment monitoring
def test_payment_monitoring(client: TestClient, admin_auth_headers: dict, db_session: Session):
    pay = Payment(
        order_id=1,
        payment_method=PaymentMethod.UPI,
        payment_status=PaymentStatus.SUCCESS,
        amount=Decimal("350.00"),
        transaction_reference="TXN-ADM-9999",
    )
    db_session.add(pay)
    db_session.commit()

    res = client.get("/api/v1/admin/payments?status=SUCCESS", headers=admin_auth_headers)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert any(p["transaction_reference"] == "TXN-ADM-9999" for p in items)


# 26. Coupon management
def test_coupon_management(client: TestClient, admin_auth_headers: dict):
    # Create coupon
    create_res = client.post(
        "/api/v1/admin/coupons",
        headers=admin_auth_headers,
        json={
            "code": "FESTIVE25",
            "discount_type": "PERCENTAGE",
            "discount_value": 25.0,
            "min_order_value": 200.0,
            "max_discount_amount": 100.0,
            "valid_from": "2026-01-01T00:00:00",
            "valid_to": "2026-12-31T23:59:59",
            "usage_limit_per_user": 3,
            "total_usage_limit": 500,
            "is_active": True,
        },
    )
    assert create_res.status_code == 201
    c_id = create_res.json()["data"]["coupon_id"]

    # Update coupon
    upd_res = client.put(
        f"/api/v1/admin/coupons/{c_id}",
        headers=admin_auth_headers,
        json={"is_active": False},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["is_active"] is False


# 27. Revenue calculation & 28. Analytics date filtering
def test_revenue_and_analytics(client: TestClient, admin_auth_headers: dict, db_session: Session):
    # Seed 1 completed order with completed payment
    o1 = Order(
        customer_id=10,
        kitchen_id=1,
        delivery_address_id=1,
        order_number=f"ORD-REV-{datetime.utcnow().strftime('%f')}",
        order_status=OrderStatus.DELIVERED,
        subtotal_amount=Decimal("500.00"),
        tax_amount=Decimal("25.00"),
        delivery_fee=Decimal("40.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("565.00"),
    )
    db_session.add(o1)
    db_session.flush()

    p1 = Payment(
        order_id=o1.order_id,
        payment_method=PaymentMethod.UPI,
        payment_status=PaymentStatus.SUCCESS,
        amount=Decimal("565.00"),
        transaction_reference=f"TXN-REV-{o1.order_id}",
    )
    db_session.add(p1)

    # Seed 1 cancelled order with completed payment (should be EXCLUDED from net revenue)
    o2 = Order(
        customer_id=10,
        kitchen_id=1,
        delivery_address_id=1,
        order_number=f"ORD-REV-CANCEL-{datetime.utcnow().strftime('%f')}",
        order_status=OrderStatus.CANCELLED,
        subtotal_amount=Decimal("400.00"),
        tax_amount=Decimal("20.00"),
        delivery_fee=Decimal("40.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("460.00"),
    )
    db_session.add(o2)
    db_session.flush()

    p2 = Payment(
        order_id=o2.order_id,
        payment_method=PaymentMethod.UPI,
        payment_status=PaymentStatus.REFUNDED,
        amount=Decimal("460.00"),
        transaction_reference=f"TXN-REV-CANCEL-{o2.order_id}",
    )
    db_session.add(p2)
    db_session.commit()

    # 28. Analytics overview with date filter
    res = client.get("/api/v1/admin/analytics/overview?days=7", headers=admin_auth_headers)
    assert res.status_code == 200
    analytics = res.json()["data"]
    assert "revenue_by_day" in analytics
    assert "orders_by_day" in analytics
    assert "order_status_distribution" in analytics
    assert "delivery_speed" in analytics

    # Check dashboard metric revenue
    dash_res = client.get("/api/v1/admin/dashboard", headers=admin_auth_headers)
    assert dash_res.status_code == 200
    stats = dash_res.json()["data"]
    assert Decimal(str(stats["total_revenue"])) >= Decimal("565.00")


# 29. Audit-log recording
def test_audit_log_recording(client: TestClient, admin_auth_headers: dict, db_session: Session):
    # Perform an action that logs audit record (create kitchen)
    client.post(
        "/api/v1/admin/kitchens",
        headers=admin_auth_headers,
        json={
            "name": "Audit Test Kitchen",
            "street_address": "Test Street",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "phone": "+918011223344",
            "email": "audit@kitchen.com",
            "max_orders_per_hour": 50,
        },
    )

    # Verify audit log was recorded in database
    log = db_session.query(AdminAuditLog).filter(AdminAuditLog.action == "CREATE_KITCHEN").first()
    assert log is not None
    assert log.actor_user_id == 40
    assert log.entity_type == "KITCHEN"

    # Verify audit logs listing API
    res = client.get("/api/v1/admin/audit-logs?action=CREATE_KITCHEN", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["meta"]["total_count"] >= 1
