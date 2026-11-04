import pytest
from datetime import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.fulfillment import Delivery, DeliveryStatus
from app.models.order import Order, OrderItem, OrderStatus, OrderStatusHistory, Payment, PaymentMethod, PaymentStatus
from app.models.user import DeliveryPerson, DeliveryPersonStatus


def _create_test_order(db: Session, customer_id: int = 10, kitchen_id: int = 1, initial_status: OrderStatus = OrderStatus.READY_FOR_PICKUP) -> Order:
    """Helper to create an order with payment and snapshot items."""
    order = Order(
        customer_id=customer_id,
        kitchen_id=kitchen_id,
        delivery_address_id=1,
        order_number=f"ORD-DEL-{datetime.utcnow().strftime('%f')}",
        order_status=initial_status,
        subtotal_amount=Decimal("320.00"),
        tax_amount=Decimal("16.00"),
        delivery_fee=Decimal("40.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("376.00"),
    )
    db.add(order)
    db.flush()

    item = OrderItem(
        order_id=order.order_id,
        menu_item_id=1,
        item_name_snapshot="Butter Chicken Rice Bowl",
        unit_price_snapshot=Decimal("320.00"),
        quantity=1,
        subtotal_price=Decimal("320.00"),
    )
    db.add(item)

    payment = Payment(
        order_id=order.order_id,
        payment_method=PaymentMethod.UPI,
        payment_status=PaymentStatus.SUCCESS,
        amount=order.total_amount,
        transaction_reference=f"TXN-DEL-{order.order_id}",
    )
    db.add(payment)

    hist = OrderStatusHistory(
        order_id=order.order_id,
        changed_by_user_id=1,
        previous_status=OrderStatus.PENDING,
        new_status=initial_status,
        notes="Order initialized for delivery test",
    )
    db.add(hist)
    db.commit()
    db.refresh(order)
    return order


# 1. Delivery login
def test_delivery_login(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "driver1@test.com", "password": "Password@123"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "access_token" in res["data"]
    assert res["data"]["user"]["role"] == "DELIVERY_PERSON"


# 2. Own profile access
def test_delivery_own_profile_access(client: TestClient, delivery_auth_headers: dict):
    response = client.get("/api/v1/delivery/profile", headers=delivery_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["delivery_person_id"] == 60
    assert data["email"] == "driver1@test.com"
    assert data["current_status"] == "AVAILABLE"
    assert data["vehicle_type"] == "MOTORCYCLE"


# 3. Assignment listing & availability toggle
def test_delivery_dashboard_and_availability(client: TestClient, delivery_auth_headers: dict):
    # Check dashboard stats
    dash_res = client.get("/api/v1/delivery/dashboard", headers=delivery_auth_headers)
    assert dash_res.status_code == 200
    assert "assigned_deliveries" in dash_res.json()["data"]

    # Toggle availability to OFF_DUTY
    toggle_res = client.patch(
        "/api/v1/delivery/availability",
        headers=delivery_auth_headers,
        json={"current_status": "OFF_DUTY"},
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["data"]["current_status"] == "OFF_DUTY"

    # Toggle back to AVAILABLE
    toggle_back = client.patch(
        "/api/v1/delivery/availability",
        headers=delivery_auth_headers,
        json={"current_status": "AVAILABLE"},
    )
    assert toggle_back.status_code == 200
    assert toggle_back.json()["data"]["current_status"] == "AVAILABLE"


# 4. Assignment listing & cross-courier isolation
def test_delivery_cross_assignment_isolation(
    client: TestClient,
    delivery_auth_headers: dict,
    other_delivery_auth_headers: dict,
    admin_auth_headers: dict,
    db_session: Session,
):
    # Create order and assign to Driver 1 (user 60)
    order = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.READY_FOR_PICKUP)
    assign_res = client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 60},
    )
    assert assign_res.status_code == 200
    del_id = assign_res.json()["data"]["delivery_id"]

    # Driver 1 can fetch assignment detail
    d1_res = client.get(f"/api/v1/delivery/assignments/{del_id}", headers=delivery_auth_headers)
    assert d1_res.status_code == 200
    assert d1_res.json()["data"]["delivery_id"] == del_id

    # Driver 2 attempting to view Driver 1's assignment MUST get 403 Forbidden
    d2_res = client.get(f"/api/v1/delivery/assignments/{del_id}", headers=other_delivery_auth_headers)
    assert d2_res.status_code == 403


# 5. Valid delivery assignment by Admin
def test_valid_delivery_assignment_by_admin(
    client: TestClient, admin_auth_headers: dict, db_session: Session
):
    # Check available personnel
    avail_res = client.get("/api/v1/admin/delivery/available-personnel", headers=admin_auth_headers)
    assert avail_res.status_code == 200
    personnel = avail_res.json()["data"]
    assert any(p["delivery_person_id"] == 61 for p in personnel)

    order = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.READY_FOR_PICKUP)
    res = client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 61},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["order_id"] == order.order_id
    assert data["delivery_status"] == "ASSIGNED"


# 6. Duplicate assignment rejection
def test_duplicate_delivery_assignment_rejection(
    client: TestClient, admin_auth_headers: dict, db_session: Session
):
    order = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.READY_FOR_PICKUP)
    res1 = client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 60},
    )
    assert res1.status_code == 200

    # Advance to PICKED_UP
    del_id = res1.json()["data"]["delivery_id"]
    delivery_record = db_session.query(Delivery).filter(Delivery.delivery_id == del_id).first()
    delivery_record.delivery_status = DeliveryStatus.PICKED_UP
    db_session.commit()

    # Re-assigning another courier to an in-transit order MUST fail with 400
    res2 = client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 61},
    )
    assert res2.status_code == 400


# 7. Unavailable personnel rejection (Off Duty courier)
def test_unavailable_personnel_rejection(
    client: TestClient, admin_auth_headers: dict, db_session: Session
):
    order = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.READY_FOR_PICKUP)
    # Courier 62 is seeded as OFF_DUTY
    res = client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 62},
    )
    assert res.status_code == 400
    assert "OFF_DUTY" in res.json()["detail"]


# 8. Valid pickup & 9. Invalid pickup before kitchen ready
def test_invalid_and_valid_pickup(
    client: TestClient,
    delivery_auth_headers: dict,
    admin_auth_headers: dict,
    db_session: Session,
):
    # Create order in PENDING status
    order_pending = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.PENDING)
    assign_res = client.post(
        f"/api/v1/admin/orders/{order_pending.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 60},
    )
    assert assign_res.status_code == 200
    del_id = assign_res.json()["data"]["delivery_id"]

    # 9. Invalid pickup: Courier tries to pick up while kitchen is still PENDING
    bad_pickup = client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        headers=delivery_auth_headers,
        json={"status": "PICKED_UP"},
    )
    assert bad_pickup.status_code == 400
    assert "READY_FOR_PICKUP" in bad_pickup.json()["detail"]

    # Now kitchen marks it READY_FOR_PICKUP
    order_pending.order_status = OrderStatus.READY_FOR_PICKUP
    db_session.commit()

    # 8. Valid pickup: Courier marks PICKED_UP
    good_pickup = client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        headers=delivery_auth_headers,
        json={"status": "PICKED_UP", "notes": "Order picked up from Indiranagar kitchen"},
    )
    assert good_pickup.status_code == 200
    assert good_pickup.json()["data"]["delivery_status"] == "PICKED_UP"


# 10. Valid delivery completion & 11. Duplicate completion rejection
def test_valid_delivery_completion_and_duplicate_rejection(
    client: TestClient,
    delivery_auth_headers: dict,
    admin_auth_headers: dict,
    db_session: Session,
):
    order = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.READY_FOR_PICKUP)
    assign_res = client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 60},
    )
    del_id = assign_res.json()["data"]["delivery_id"]

    # Advance to PICKED_UP
    client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        headers=delivery_auth_headers,
        json={"status": "PICKED_UP"},
    )

    # Advance to OUT_FOR_DELIVERY
    client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        headers=delivery_auth_headers,
        json={"status": "OUT_FOR_DELIVERY"},
    )

    # 10. Valid completion
    complete_res = client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        headers=delivery_auth_headers,
        json={"status": "DELIVERED", "notes": "Handed to customer at door"},
    )
    assert complete_res.status_code == 200
    data = complete_res.json()["data"]
    assert data["delivery_status"] == "DELIVERED"
    assert data["order_status"] == "DELIVERED"

    # Verify courier is automatically set back to AVAILABLE
    driver = db_session.query(DeliveryPerson).filter(DeliveryPerson.delivery_person_id == 60).first()
    assert driver.current_status == DeliveryPersonStatus.AVAILABLE

    # 11. Duplicate completion rejection
    dup_res = client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        headers=delivery_auth_headers,
        json={"status": "DELIVERED"},
    )
    assert dup_res.status_code == 400
    assert "already marked as DELIVERED" in dup_res.json()["detail"]


# 12. Customer tracking access & 13. Cross-customer tracking rejection
def test_customer_tracking_and_cross_customer_isolation(
    client: TestClient,
    customer_auth_headers: dict,
    other_customer_auth_headers: dict,
    admin_auth_headers: dict,
    db_session: Session,
):
    # Customer 10 places order
    order = _create_test_order(db_session, customer_id=10, initial_status=OrderStatus.READY_FOR_PICKUP)

    # Admin assigns courier
    client.post(
        f"/api/v1/admin/orders/{order.order_id}/assign-delivery",
        headers=admin_auth_headers,
        json={"delivery_person_id": 60},
    )

    # 12. Customer 10 views tracking of own order
    track_res = client.get(f"/api/v1/orders/{order.order_id}/tracking", headers=customer_auth_headers)
    assert track_res.status_code == 200
    track_data = track_res.json()["data"]
    assert track_data["order_id"] == order.order_id
    assert track_data["delivery_status"] == "ASSIGNED"
    assert "timeline" in track_data
    assert len(track_data["timeline"]) >= 1

    # 13. Customer 20 (other customer) attempting to track Customer 10's order MUST receive 403 Forbidden
    unauth_res = client.get(f"/api/v1/orders/{order.order_id}/tracking", headers=other_customer_auth_headers)
    assert unauth_res.status_code == 403
