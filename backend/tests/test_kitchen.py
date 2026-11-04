import pytest
from decimal import Decimal
from app.models.order import OrderStatus


def test_kitchen_manager_and_staff_access(client, kitchen_manager_headers, kitchen_staff_headers, customer_auth_headers):
    # 1. Kitchen Manager access
    resp = client.get("/api/v1/kitchen/me", headers=kitchen_manager_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["kitchen_id"] == 1
    assert data["staff_role"] == "KITCHEN_MANAGER"

    # 2. Kitchen Staff access
    resp_staff = client.get("/api/v1/kitchen/me", headers=kitchen_staff_headers)
    assert resp_staff.status_code == 200
    assert resp_staff.json()["data"]["staff_role"] == "LINE_COOK"

    # 3. Customer access rejection (403 Forbidden)
    resp_cust = client.get("/api/v1/kitchen/me", headers=customer_auth_headers)
    assert resp_cust.status_code == 403

    # Unauthenticated rejection (401 Unauthorized)
    resp_unauth = client.get("/api/v1/kitchen/me")
    assert resp_unauth.status_code == 401


def test_kitchen_dashboard_and_cross_kitchen_isolation(client, kitchen_manager_headers, kitchen2_staff_headers):
    # 4 & 5. Dashboard stats and cross-kitchen data isolation
    resp = client.get("/api/v1/kitchen/dashboard", headers=kitchen_manager_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["kitchen_id"] == 1
    assert "total_orders_today" in data
    assert "low_stock_count" in data
    assert data["low_stock_count"] >= 1  # Paneer has 2kg vs 5kg reorder

    # Kitchen 2 staff accessing their separate dashboard
    resp2 = client.get("/api/v1/kitchen/dashboard", headers=kitchen2_staff_headers)
    assert resp2.status_code == 200
    assert resp2.json()["data"]["kitchen_id"] == 2


def test_kitchen_order_management_workflow(client, customer_auth_headers, kitchen_staff_headers, kitchen2_staff_headers):
    # Customer creates an order for Kitchen 1
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_res = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "k-order-test-01"},
        headers=customer_auth_headers,
    )
    assert order_res.status_code in [200, 201]
    order_id = order_res.json()["data"]["order_id"]

    # 6. Kitchen order listing for Kitchen 1
    list_res = client.get("/api/v1/kitchen/orders", headers=kitchen_staff_headers)
    assert list_res.status_code == 200
    assert any(o["order_id"] == order_id for o in list_res.json()["data"]["items"])

    # Cross-kitchen isolation: Kitchen 2 staff cannot see Kitchen 1 orders
    list_res2 = client.get("/api/v1/kitchen/orders", headers=kitchen2_staff_headers)
    assert list_res2.status_code == 200
    assert not any(o["order_id"] == order_id for o in list_res2.json()["data"]["items"])

    # 7. Order details for assigned kitchen
    det_res = client.get(f"/api/v1/kitchen/orders/{order_id}", headers=kitchen_staff_headers)
    assert det_res.status_code == 200
    assert det_res.json()["data"]["order_id"] == order_id
    assert len(det_res.json()["data"]["items"]) == 1

    # Unauthorized cross-kitchen order details access (404)
    det_res2 = client.get(f"/api/v1/kitchen/orders/{order_id}", headers=kitchen2_staff_headers)
    assert det_res2.status_code == 404

    # 8. Valid status transition: PENDING -> CONFIRMED
    tr1 = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "CONFIRMED", "notes": "Manager confirmed order"},
        headers=kitchen_staff_headers,
    )
    assert tr1.status_code == 200
    assert tr1.json()["data"]["order_status"] == "CONFIRMED"

    # 10. Duplicate status update (idempotent 200)
    tr_dup = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "CONFIRMED"},
        headers=kitchen_staff_headers,
    )
    assert tr_dup.status_code == 200
    assert tr_dup.json()["data"]["order_status"] == "CONFIRMED"

    # 13. Kitchen CANNOT mark order DELIVERED (403 Forbidden)
    tr_deliv = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "DELIVERED"},
        headers=kitchen_staff_headers,
    )
    assert tr_deliv.status_code == 403

    # 9. Invalid transition (CONFIRMED cannot jump directly to DELIVERED or invalid sequence)
    # Transition CONFIRMED -> PREPARING (Valid, triggers recipe inventory deduction)
    tr2 = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "PREPARING", "notes": "Chef started cooking"},
        headers=kitchen_staff_headers,
    )
    assert tr2.status_code == 200
    assert tr2.json()["data"]["order_status"] == "PREPARING"

    # 11. Status history recording
    det_after = client.get(f"/api/v1/kitchen/orders/{order_id}", headers=kitchen_staff_headers)
    timeline = det_after.json()["data"]["timeline"]
    assert len(timeline) >= 3  # Initial placed, CONFIRMED, PREPARING
    assert any(h["new_status"] == "PREPARING" for h in timeline)


def test_kitchen_order_queue(client, customer_auth_headers, kitchen_staff_headers):
    # Customer orders
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_res = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "k-queue-test-01"},
        headers=customer_auth_headers,
    )
    assert order_res.status_code in [200, 201]
    order_id = order_res.json()["data"]["order_id"]

    # Queue retrieval
    resp = client.get("/api/v1/kitchen/queue", headers=kitchen_staff_headers)
    assert resp.status_code == 200
    queue = resp.json()["data"]
    assert any(q["order_id"] == order_id for q in queue)


def test_kitchen_menu_crud_and_permissions(client, kitchen_manager_headers, kitchen_staff_headers, kitchen2_staff_headers):
    # 14. Create menu item (Manager permitted)
    create_payload = {
        "name": "Smoked Tandoori Chicken Skewers",
        "category_id": 1,
        "description": "Charcoal grilled skewers with mint glaze",
        "base_price": 280.00,
        "is_vegetarian": False,
        "is_available": True,
        "preparation_time_minutes": 20,
        "calories": 420,
    }
    resp = client.post("/api/v1/kitchen/menu", json=create_payload, headers=kitchen_manager_headers)
    assert resp.status_code == 201
    new_item = resp.json()["data"]
    item_id = new_item["menu_item_id"]
    assert new_item["name"] == "Smoked Tandoori Chicken Skewers"

    # Staff (non-manager) cannot create items (403 Forbidden)
    resp_staff_create = client.post("/api/v1/kitchen/menu", json=create_payload, headers=kitchen_staff_headers)
    assert resp_staff_create.status_code == 403

    # 17. Invalid category (400 Bad Request)
    bad_cat_payload = dict(create_payload, category_id=99999, name="Unique Name 123")
    assert client.post("/api/v1/kitchen/menu", json=bad_cat_payload, headers=kitchen_manager_headers).status_code == 400

    # 15. Update menu item (Manager permitted)
    update_res = client.put(
        f"/api/v1/kitchen/menu/{item_id}",
        json={"base_price": 295.00, "description": "Updated spices"},
        headers=kitchen_manager_headers,
    )
    assert update_res.status_code == 200
    assert float(update_res.json()["data"]["base_price"]) == 295.00

    # 18. Cross-kitchen menu modification rejection (404/403)
    # Kitchen 2 staff trying to modify Kitchen 1's dish
    resp_cross = client.put(
        f"/api/v1/kitchen/menu/{item_id}",
        json={"base_price": 100.00},
        headers=kitchen2_staff_headers,
    )
    assert resp_cross.status_code in [403, 404]

    # 16. Availability toggle (Allowed for all kitchen staff)
    avail_res = client.patch(
        f"/api/v1/kitchen/menu/{item_id}/availability",
        json={"is_available": False},
        headers=kitchen_staff_headers,
    )
    assert avail_res.status_code == 200
    assert avail_res.json()["data"]["is_available"] is False


def test_kitchen_availability_operating_status(client, kitchen_manager_headers, kitchen_staff_headers):
    # View availability
    resp = client.get("/api/v1/kitchen/availability", headers=kitchen_staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["operating_status"] == "ACTIVE"

    # Manager updates availability to INACTIVE (temporarily pause orders)
    patch_res = client.patch(
        "/api/v1/kitchen/availability",
        json={"operating_status": "INACTIVE", "max_active_orders": 30},
        headers=kitchen_manager_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["operating_status"] == "INACTIVE"
    assert patch_res.json()["data"]["max_active_orders"] == 30

    # Line cook cannot change operating status (403 Forbidden)
    assert client.patch(
        "/api/v1/kitchen/availability",
        json={"operating_status": "ACTIVE"},
        headers=kitchen_staff_headers,
    ).status_code == 403
