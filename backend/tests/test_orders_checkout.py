def test_checkout_summary_and_validation(client, customer_auth_headers):
    # Ensure item in cart
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)

    # Summary
    summary_resp = client.get("/api/v1/checkout/summary?address_id=1", headers=customer_auth_headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()["data"]
    assert float(summary["subtotal_amount"]) == 320.00
    assert summary["can_place_order"] is True

    # Validate with address belonging to another customer (address_id=2 belongs to Customer 20)
    invalid_addr_resp = client.post(
        "/api/v1/checkout/validate", json={"delivery_address_id": 2}, headers=customer_auth_headers
    )
    assert invalid_addr_resp.status_code == 200
    assert invalid_addr_resp.json()["data"]["can_place_order"] is False
    assert any("does not belong" in err for err in invalid_addr_resp.json()["data"]["validation_errors"])


def test_order_placement_and_cancellation(client, customer_auth_headers):
    # Setup cart
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)

    # Place Order with idempotency key
    payload = {
        "delivery_address_id": 1,
        "payment_method": "UPI",
        "special_instructions": "Leave at front desk",
        "idempotency_key": "test-order-key-12345",
    }
    order_resp = client.post("/api/v1/orders", json=payload, headers=customer_auth_headers)
    assert order_resp.status_code == 201
    order_data = order_resp.json()["data"]
    assert "order_number" in order_data
    assert order_data["order_status"] == "PENDING"
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["item_name_snapshot"] == "Butter Chicken Rice Bowl"

    order_id = order_data["order_id"]

    # Test idempotency: submit identical order with same idempotency key
    dup_resp = client.post("/api/v1/orders", json=payload, headers=customer_auth_headers)
    assert dup_resp.status_code == 201
    assert dup_resp.json()["data"]["order_id"] == order_id  # Returns existing order

    # Verify cart was automatically cleared
    cart_check = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert len(cart_check.json()["data"]["items"]) == 0

    # Retrieve order detail
    detail_resp = client.get(f"/api/v1/orders/{order_id}", headers=customer_auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["order_id"] == order_id

    # Cancel order
    cancel_resp = client.post(
        f"/api/v1/orders/{order_id}/cancel", json={"reason": "Changed my mind"}, headers=customer_auth_headers
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["data"]["order_status"] == "CANCELLED"


def test_unauthorized_order_access(client, customer_auth_headers, other_customer_auth_headers):
    # Customer 1 creates an order
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "unauth-order-test-11"},
        headers=customer_auth_headers,
    )
    order_id = order_resp.json()["data"]["order_id"]

    # Customer 2 attempts to view Customer 1's order
    other_view = client.get(f"/api/v1/orders/{order_id}", headers=other_customer_auth_headers)
    assert other_view.status_code == 404

    # Customer 2 attempts to cancel Customer 1's order
    other_cancel = client.post(
        f"/api/v1/orders/{order_id}/cancel", json={"reason": "Malicious cancel"}, headers=other_customer_auth_headers
    )
    assert other_cancel.status_code == 404


def test_invalid_order_cancellation(client, customer_auth_headers):
    # Setup and place order
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "inv-cancel-key-22"},
        headers=customer_auth_headers,
    )
    order_id = order_resp.json()["data"]["order_id"]

    # First cancel succeeds
    client.post(f"/api/v1/orders/{order_id}/cancel", json={"reason": "Reason 1"}, headers=customer_auth_headers)

    # Second cancel must fail (cannot cancel already cancelled order)
    repeat_cancel = client.post(
        f"/api/v1/orders/{order_id}/cancel", json={"reason": "Reason 2"}, headers=customer_auth_headers
    )
    assert repeat_cancel.status_code == 400
    assert "cannot be cancelled" in repeat_cancel.json()["detail"].lower()


def test_orders_listing(client, customer_auth_headers):
    list_resp = client.get("/api/v1/orders?page=1&page_size=10", headers=customer_auth_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()["data"]
    assert "items" in data
    assert "meta" in data
    assert data["meta"]["page"] == 1
