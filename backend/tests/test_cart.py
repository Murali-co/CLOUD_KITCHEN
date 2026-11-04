def test_cart_workflow(client, customer_auth_headers):
    # 1. Clear cart initially
    client.delete("/api/v1/cart", headers=customer_auth_headers)

    # 2. Add dish 1 (Butter Chicken, Kitchen 1)
    add_resp = client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 2}, headers=customer_auth_headers)
    assert add_resp.status_code == 200
    cart = add_resp.json()["data"]
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert float(cart["subtotal_amount"]) == 640.00

    # 3. Add dish 2 (Margherita Pizza, Kitchen 1)
    add_resp2 = client.post("/api/v1/cart/items", json={"menu_item_id": 2, "quantity": 1}, headers=customer_auth_headers)
    assert add_resp2.status_code == 200
    cart2 = add_resp2.json()["data"]
    assert len(cart2["items"]) == 2
    assert float(cart2["subtotal_amount"]) == 1020.00

    # 4. Mixed-kitchen cart rejection: attempt to add dish 4 (from Kitchen 2)
    mixed_resp = client.post("/api/v1/cart/items", json={"menu_item_id": 4, "quantity": 1}, headers=customer_auth_headers)
    assert mixed_resp.status_code == 400
    assert "different kitchen" in mixed_resp.json()["detail"].lower()

    # 5. Add unavailable item rejection: attempt to add dish 3 (is_available=False)
    unavail_resp = client.post("/api/v1/cart/items", json={"menu_item_id": 3, "quantity": 1}, headers=customer_auth_headers)
    assert unavail_resp.status_code == 400
    assert "unavailable" in unavail_resp.json()["detail"].lower()

    # 6. Apply valid coupon
    coupon_resp = client.post("/api/v1/cart/apply-coupon", json={"coupon_code": "TEST50"}, headers=customer_auth_headers)
    assert coupon_resp.status_code == 200
    cart_coupon = coupon_resp.json()["data"]
    assert cart_coupon["applied_coupon_code"] == "TEST50"
    assert float(cart_coupon["discount_amount"]) == 150.00  # Capped at max 150

    # 7. Remove item
    del_item = client.delete("/api/v1/cart/items/2", headers=customer_auth_headers)
    assert del_item.status_code == 200
    assert len(del_item.json()["data"]["items"]) == 1

    # 8. Clear cart
    clear_resp = client.delete("/api/v1/cart", headers=customer_auth_headers)
    assert clear_resp.status_code == 200
    assert clear_resp.json()["data"]["cleared"] is True


def test_apply_expired_coupon(client, customer_auth_headers):
    # Ensure item in cart
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    response = client.post("/api/v1/cart/apply-coupon", json={"coupon_code": "EXPIRED10"}, headers=customer_auth_headers)
    assert response.status_code == 400
    assert "not active" in response.json()["detail"].lower()
    client.delete("/api/v1/cart", headers=customer_auth_headers)


def test_cart_quantity_validation(client, customer_auth_headers):
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    # Zero quantity rejection
    zero_resp = client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 0}, headers=customer_auth_headers)
    assert zero_resp.status_code == 422

    # Negative quantity rejection
    neg_resp = client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": -5}, headers=customer_auth_headers)
    assert neg_resp.status_code == 422


def test_cart_invalid_item_rejection(client, customer_auth_headers):
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    # Non-existent item id 99999
    bad_resp = client.post("/api/v1/cart/items", json={"menu_item_id": 99999, "quantity": 1}, headers=customer_auth_headers)
    assert bad_resp.status_code == 404


def test_cart_remove_coupon(client, customer_auth_headers):
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    client.post("/api/v1/cart/apply-coupon", json={"coupon_code": "TEST50"}, headers=customer_auth_headers)

    # Remove coupon
    rm_resp = client.delete("/api/v1/cart/remove-coupon", headers=customer_auth_headers)
    assert rm_resp.status_code == 200
    assert rm_resp.json()["data"]["applied_coupon_code"] is None
    assert float(rm_resp.json()["data"]["discount_amount"]) == 0.00
