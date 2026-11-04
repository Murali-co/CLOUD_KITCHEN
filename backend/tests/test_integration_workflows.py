import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
import redis

from app.db.redis import redis_client


def test_workflow_a_customer_order(client):
    """
    Workflow A: Customer Order Full Lifecycle
    Register -> Login -> Browse kitchen -> Add food -> Apply coupon -> Checkout -> Test payment -> Order history -> Tracking
    """
    # 1. Register customer
    reg_payload = {
        "full_name": "Arjun Reddy",
        "email": "workflow_cust@test.com",
        "phone_number": "+919876543210",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    reg_resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201

    # 2. Login verification
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "workflow_cust@test.com", "password": "Password@123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Browse kitchens
    k_resp = client.get("/api/v1/kitchens")
    assert k_resp.status_code == 200
    kitchens = k_resp.json()["data"]["items"]
    assert len(kitchens) >= 1
    kitchen_id = kitchens[0]["kitchen_id"]

    # 4. Browse menu
    menu_resp = client.get(f"/api/v1/menu?kitchen_id={kitchen_id}")
    assert menu_resp.status_code == 200
    menu_items = menu_resp.json()["data"]["items"]
    assert len(menu_items) >= 1
    dish_id = menu_items[0]["menu_item_id"]

    # 5. Add to cart & apply coupon
    client.delete("/api/v1/cart", headers=auth_headers)
    add_resp = client.post(
        "/api/v1/cart/items",
        json={"menu_item_id": dish_id, "quantity": 2, "customization_notes": "Extra spicy"},
        headers=auth_headers,
    )
    assert add_resp.status_code == 200

    coupon_resp = client.post(
        "/api/v1/cart/apply-coupon",
        json={"coupon_code": "TEST50"},
        headers=auth_headers,
    )
    assert coupon_resp.status_code == 200

    # 6. Add delivery address
    addr_payload = {
        "address_label": "Home",
        "recipient_name": "Arjun Reddy",
        "recipient_phone": "+919876543210",
        "address_line1": "Flat 402, Green Meadows",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
        "is_default": True,
    }
    addr_resp = client.post("/api/v1/customer/addresses", json=addr_payload, headers=auth_headers)
    assert addr_resp.status_code == 201
    address_id = addr_resp.json()["data"]["address_id"]

    # 7. Validate checkout summary
    chk_resp = client.post(
        "/api/v1/checkout/validate",
        json={"delivery_address_id": address_id},
        headers=auth_headers,
    )
    assert chk_resp.status_code == 200
    assert chk_resp.json()["data"]["can_place_order"] is True

    # 8. Place Order
    order_payload = {
        "delivery_address_id": address_id,
        "payment_method": "UPI",
        "special_instructions": "Ring bell twice",
        "idempotency_key": "workflow-a-idemp-001",
    }
    order_resp = client.post("/api/v1/orders", json=order_payload, headers=auth_headers)
    assert order_resp.status_code == 201
    order_data = order_resp.json()["data"]
    order_id = order_data["order_id"]
    assert order_data["order_status"] == "PENDING"

    # 9. Test Payment
    pay_create = client.post(
        "/api/v1/payments/create",
        json={"order_id": order_id, "payment_method": "UPI"},
        headers=auth_headers,
    )
    assert pay_create.status_code == 200
    pay_data = pay_create.json()["data"]

    pay_verify = client.post(
        "/api/v1/payments/verify",
        json={
            "order_id": order_id,
            "transaction_reference": pay_data["transaction_reference"],
            "signature": pay_data["test_signature"],
        },
        headers=auth_headers,
    )
    assert pay_verify.status_code == 200
    assert pay_verify.json()["data"]["payment_status"] == "SUCCESS"

    # 10. Order history & status
    history_resp = client.get("/api/v1/orders", headers=auth_headers)
    assert history_resp.status_code == 200
    assert any(o["order_id"] == order_id for o in history_resp.json()["data"]["items"])

    order_check = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
    assert order_check.status_code == 200
    assert order_check.json()["data"]["order_status"] == "CONFIRMED"


def test_workflow_b_kitchen_fulfilment(client, customer_auth_headers, kitchen_manager_headers, kitchen_staff_headers):
    """
    Workflow B: Kitchen Fulfilment
    Kitchen login -> View order in queue -> Confirm -> Prepare -> Deduct inventory -> Mark ready
    """
    # Setup order from customer
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "wf-b-idemp-001"},
        headers=customer_auth_headers,
    )
    assert order_resp.status_code == 201
    order_id = order_resp.json()["data"]["order_id"]

    # 1. Kitchen Manager views dashboard
    dash_resp = client.get("/api/v1/kitchen/dashboard", headers=kitchen_manager_headers)
    assert dash_resp.status_code == 200
    assert dash_resp.json()["data"]["kitchen_id"] == 1

    # 2. View queue
    queue_resp = client.get("/api/v1/kitchen/orders", headers=kitchen_manager_headers)
    assert queue_resp.status_code == 200
    orders = queue_resp.json()["data"]["items"]
    assert any(o["order_id"] == order_id for o in orders)

    # 3. Confirm order
    conf_resp = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "CONFIRMED", "notes": "Order accepted by kitchen"},
        headers=kitchen_staff_headers,
    )
    assert conf_resp.status_code == 200
    assert conf_resp.json()["data"]["order_status"] == "CONFIRMED"

    # 4. Transition to PREPARING
    prep_resp = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "PREPARING", "notes": "Chef started cooking"},
        headers=kitchen_staff_headers,
    )
    assert prep_resp.status_code == 200
    assert prep_resp.json()["data"]["order_status"] == "PREPARING"

    # 5. Transition to READY_FOR_PICKUP (triggers recipe inventory deduction)
    ready_resp = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "READY_FOR_PICKUP", "notes": "Packed and ready"},
        headers=kitchen_staff_headers,
    )
    assert ready_resp.status_code == 200
    assert ready_resp.json()["data"]["order_status"] == "READY_FOR_PICKUP"

    # 6. Verify stock deduction
    inv_resp = client.get("/api/v1/kitchen/inventory/1", headers=kitchen_staff_headers)
    assert inv_resp.status_code == 200
    # Rice initial was 50.000, 1 portion requires 0.150kg -> 49.850kg
    assert float(inv_resp.json()["data"]["current_stock"]) == 49.85


def test_workflow_c_delivery(client, customer_auth_headers, admin_auth_headers, delivery_auth_headers, kitchen_staff_headers):
    """
    Workflow C: Delivery Workflow
    Admin assigns delivery -> Delivery login -> Pickup -> Out for delivery -> Delivered
    """
    # 1. Customer places order
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "wf-c-idemp-001"},
        headers=customer_auth_headers,
    )
    assert order_resp.status_code == 201
    order_id = order_resp.json()["data"]["order_id"]

    # Advance order to READY_FOR_PICKUP via kitchen
    client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "CONFIRMED"},
        headers=kitchen_staff_headers,
    )
    client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers=kitchen_staff_headers,
    )
    client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "READY_FOR_PICKUP"},
        headers=kitchen_staff_headers,
    )

    # 2. Admin assigns delivery person (ID 60)
    assign_resp = client.post(
        f"/api/v1/admin/orders/{order_id}/assign-delivery",
        json={"delivery_person_id": 60},
        headers=admin_auth_headers,
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["data"]["delivery_status"] == "ASSIGNED"
    del_id = assign_resp.json()["data"]["delivery_id"]

    # 3. Delivery person views assignment
    my_tasks = client.get("/api/v1/delivery/assignments", headers=delivery_auth_headers)
    assert my_tasks.status_code == 200
    assert any(a["delivery_id"] == del_id for a in my_tasks.json()["data"]["items"])

    # 4. Delivery person picks up order -> OUT_FOR_DELIVERY
    pickup_resp = client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        json={"status": "PICKED_UP", "notes": "Order picked up from kitchen"},
        headers=delivery_auth_headers,
    )
    assert pickup_resp.status_code == 200
    assert pickup_resp.json()["data"]["delivery_status"] == "PICKED_UP"

    # Verify customer tracking reflects PICKED_UP
    track_resp = client.get(f"/api/v1/orders/{order_id}/tracking", headers=customer_auth_headers)
    assert track_resp.status_code == 200
    assert track_resp.json()["data"]["delivery_status"] == "PICKED_UP"

    # 5. Delivery person completes delivery -> DELIVERED
    deliver_resp = client.patch(
        f"/api/v1/delivery/assignments/{del_id}/status",
        json={"status": "DELIVERED", "notes": "Handed to customer"},
        headers=delivery_auth_headers,
    )
    assert deliver_resp.status_code == 200
    assert deliver_resp.json()["data"]["delivery_status"] == "DELIVERED"

    # Verify final customer tracking is DELIVERED
    final_track = client.get(f"/api/v1/orders/{order_id}/tracking", headers=customer_auth_headers)
    assert final_track.json()["data"]["delivery_status"] == "DELIVERED"


def test_workflow_d_inventory_and_recipe(client, kitchen_manager_headers, kitchen_staff_headers):
    """
    Workflow D: Inventory Management & Recipe Configuration
    Add ingredient -> Add stock -> Configure recipe -> Verify low stock threshold -> Movement history
    """
    # 1. Add ingredient
    ing_payload = {
        "name": "Organic Olive Oil",
        "category": "Oils",
        "unit_of_measure": "LITER",
        "initial_stock": 5.0,
        "reorder_level": 2.0,
    }
    ing_resp = client.post("/api/v1/kitchen/ingredients", json=ing_payload, headers=kitchen_staff_headers)
    assert ing_resp.status_code == 201
    ingredient_id = ing_resp.json()["data"]["ingredient_id"]

    # 2. Add stock (Stock-in)
    stock_payload = {
        "ingredient_id": ingredient_id,
        "quantity": 10.0,
        "unit_cost": 450.0,
        "notes": "Initial batch arrival",
    }
    stock_resp = client.post("/api/v1/kitchen/inventory/stock-in", json=stock_payload, headers=kitchen_staff_headers)
    assert stock_resp.status_code == 200
    assert float(stock_resp.json()["data"]["quantity_delta"]) == 10.0

    # 3. Configure recipe for Dish 2 (Margherita Pizza)
    recipe_payload = {
        "ingredients": [
            {"ingredient_id": ingredient_id, "quantity_required": 0.05, "unit_of_measure": "LITER"}
        ]
    }
    rec_resp = client.put(
        "/api/v1/kitchen/menu/2/recipe",
        json=recipe_payload,
        headers=kitchen_manager_headers,
    )
    assert rec_resp.status_code == 200

    # 4. View movement history
    mov_resp = client.get("/api/v1/kitchen/inventory/movements", headers=kitchen_staff_headers)
    assert mov_resp.status_code == 200
    assert any(m["ingredient_id"] == ingredient_id for m in mov_resp.json()["data"]["items"])


def test_workflow_e_administration(client, admin_auth_headers):
    """
    Workflow E: Platform Administration
    Admin login -> View metrics -> Create kitchen -> Manage categories & menu -> View orders -> View analytics
    """
    # 1. View platform metrics
    metrics_resp = client.get("/api/v1/admin/dashboard", headers=admin_auth_headers)
    assert metrics_resp.status_code == 200
    assert "total_users" in metrics_resp.json()["data"]

    # 2. Create kitchen
    k_payload = {
        "name": "Whitefield Cloud Kitchen",
        "street_address": "ITPL Main Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560066",
        "phone": "+918099887766",
        "email": "whitefield@cloudkitchen.com",
    }
    k_create = client.post("/api/v1/admin/kitchens", json=k_payload, headers=admin_auth_headers)
    assert k_create.status_code == 201
    new_k_id = k_create.json()["data"]["kitchen_id"]

    # 3. Create Category
    cat_payload = {"name": "Artisan Beverages", "description": "Craft drinks and iced teas"}
    cat_resp = client.post("/api/v1/admin/categories", json=cat_payload, headers=admin_auth_headers)
    assert cat_resp.status_code == 201

    # 4. Toggle Menu item availability
    toggle_resp = client.patch(
        "/api/v1/admin/menu/1/status",
        json={"is_available": True},
        headers=admin_auth_headers,
    )
    assert toggle_resp.status_code == 200

    # 5. View orders
    admin_orders = client.get("/api/v1/admin/orders", headers=admin_auth_headers)
    assert admin_orders.status_code == 200
    assert "items" in admin_orders.json()["data"]

    # 6. View revenue analytics
    analytics_resp = client.get("/api/v1/admin/analytics/overview?days=7", headers=admin_auth_headers)
    assert analytics_resp.status_code == 200
    assert "total_orders" in analytics_resp.json()["data"]


def test_concurrency_and_data_consistency(client, customer_auth_headers, admin_auth_headers, kitchen_staff_headers):
    """
    Tests idempotency, duplicate prevention, and consistency.
    """
    # 1. Setup cart
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)

    order_payload = {
        "delivery_address_id": 1,
        "payment_method": "CASH_ON_DELIVERY",
        "idempotency_key": "concurrent-test-key-55555",
    }

    # First submission
    resp1 = client.post("/api/v1/orders", json=order_payload, headers=customer_auth_headers)
    assert resp1.status_code == 201
    order_id1 = resp1.json()["data"]["order_id"]

    # Concurrent/duplicate submission with same idempotency key
    resp2 = client.post("/api/v1/orders", json=order_payload, headers=customer_auth_headers)
    assert resp2.status_code == 201
    order_id2 = resp2.json()["data"]["order_id"]

    # Must match exactly, not create two rows
    assert order_id1 == order_id2

    # 2. Advance to READY_FOR_PICKUP
    client.patch(
        f"/api/v1/kitchen/orders/{order_id1}/status",
        json={"status": "CONFIRMED"},
        headers=kitchen_staff_headers,
    )
    client.patch(
        f"/api/v1/kitchen/orders/{order_id1}/status",
        json={"status": "PREPARING"},
        headers=kitchen_staff_headers,
    )
    client.patch(
        f"/api/v1/kitchen/orders/{order_id1}/status",
        json={"status": "READY_FOR_PICKUP"},
        headers=kitchen_staff_headers,
    )

    # 3. Assign delivery person
    assign1 = client.post(
        f"/api/v1/admin/orders/{order_id1}/assign-delivery",
        json={"delivery_person_id": 60},
        headers=admin_auth_headers,
    )
    assert assign1.status_code == 200
    del_id = assign1.json()["data"]["delivery_id"]

    # Transition to PICKED_UP
    from app.core.security import create_access_token
    d_headers = {"Authorization": f"Bearer {create_access_token(subject=60)}"}
    client.patch(f"/api/v1/delivery/assignments/{del_id}/status", json={"status": "PICKED_UP"}, headers=d_headers)

    # Re-assigning an in-transit order must fail with 400
    assign2 = client.post(
        f"/api/v1/admin/orders/{order_id1}/assign-delivery",
        json={"delivery_person_id": 61},
        headers=admin_auth_headers,
    )
    assert assign2.status_code == 400


def test_redis_failure_and_degraded_operation(client):
    """
    Tests graceful degradation when Redis connection fails.
    - Application health endpoint reports degraded status when MySQL is up but Redis is down.
    - Permanent database-backed catalog operations continue working seamlessly.
    """
    mock_failing_client = MagicMock()
    mock_failing_client.ping.side_effect = redis.ConnectionError("Redis cluster unreachable")
    mock_failing_client.get.side_effect = redis.ConnectionError("Redis cluster unreachable")
    mock_failing_client.set.side_effect = redis.ConnectionError("Redis cluster unreachable")

    orig_client = redis_client._client
    redis_client._client = mock_failing_client

    try:
        with patch("app.api.routes.health.check_db_connectivity") as mock_db:
            mock_db.return_value = {"status": "connected", "available": True, "detail": "MySQL primary online"}

            # 1. Health check reports degraded status
            health_resp = client.get("/api/v1/health")
            assert health_resp.status_code == 200
            health_data = health_resp.json()
            assert health_data["api_status"] == "degraded"
            assert health_data["mysql"]["available"] is True
            assert health_data["redis"]["available"] is False

        # 2. Kitchen browsing continues operating via database
        kitchens_resp = client.get("/api/v1/kitchens")
        assert kitchens_resp.status_code == 200
        assert len(kitchens_resp.json()["data"]["items"]) >= 1

        # 3. Menu search continues operating via database
        menu_resp = client.get("/api/v1/menu")
        assert menu_resp.status_code == 200
        assert len(menu_resp.json()["data"]["items"]) >= 1
    finally:
        redis_client._client = orig_client
