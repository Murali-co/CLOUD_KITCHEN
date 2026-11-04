def test_payment_workflow(client, customer_auth_headers):
    # Setup order
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={
            "delivery_address_id": 1,
            "payment_method": "UPI",
            "idempotency_key": "payment-test-key-9988",
        },
        headers=customer_auth_headers,
    )
    order_id = order_resp.json()["data"]["order_id"]

    # 1. Create payment order
    create_pay = client.post(
        "/api/v1/payments/create", json={"order_id": order_id, "payment_method": "UPI"}, headers=customer_auth_headers
    )
    assert create_pay.status_code == 200
    pay_data = create_pay.json()["data"]
    assert "transaction_reference" in pay_data
    assert "test_signature" in pay_data

    # 2. Verify with valid signature
    verify_resp = client.post(
        "/api/v1/payments/verify",
        json={
            "order_id": order_id,
            "transaction_reference": pay_data["transaction_reference"],
            "signature": pay_data["test_signature"],
        },
        headers=customer_auth_headers,
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["data"]["payment_status"] == "SUCCESS"

    # Verify order advanced to CONFIRMED
    order_check = client.get(f"/api/v1/orders/{order_id}", headers=customer_auth_headers)
    assert order_check.json()["data"]["order_status"] == "CONFIRMED"


def test_payment_invalid_signature_rejection(client, customer_auth_headers):
    # Setup order
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={
            "delivery_address_id": 1,
            "payment_method": "UPI",
            "idempotency_key": "payment-fail-key-7766",
        },
        headers=customer_auth_headers,
    )
    order_id = order_resp.json()["data"]["order_id"]

    # Create payment order
    create_pay = client.post(
        "/api/v1/payments/create", json={"order_id": order_id, "payment_method": "UPI"}, headers=customer_auth_headers
    )
    pay_data = create_pay.json()["data"]

    # Submit invalid signature
    bad_verify = client.post(
        "/api/v1/payments/verify",
        json={
            "order_id": order_id,
            "transaction_reference": pay_data["transaction_reference"],
            "signature": "bogus_signature_12345",
        },
        headers=customer_auth_headers,
    )
    assert bad_verify.status_code == 400
    assert "verification failed" in bad_verify.json()["detail"].lower()


def test_payment_status_retrieval(client, customer_auth_headers):
    # Setup order
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "UPI", "idempotency_key": "pay-status-key-55"},
        headers=customer_auth_headers,
    )
    order_id = order_resp.json()["data"]["order_id"]

    create_pay = client.post(
        "/api/v1/payments/create", json={"order_id": order_id, "payment_method": "UPI"}, headers=customer_auth_headers
    )
    payment_id = create_pay.json()["data"]["payment_id"]

    # Retrieve payment record
    get_pay = client.get(f"/api/v1/payments/{payment_id}", headers=customer_auth_headers)
    assert get_pay.status_code == 200
    assert get_pay.json()["data"]["payment_id"] == payment_id
    assert get_pay.json()["data"]["order_id"] == order_id


def test_payment_repeated_webhook_idempotency(client, customer_auth_headers):
    # Setup order and payment
    client.delete("/api/v1/cart", headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_resp = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "UPI", "idempotency_key": "webhook-idemp-key-66"},
        headers=customer_auth_headers,
    )
    order_id = order_resp.json()["data"]["order_id"]
    create_pay = client.post(
        "/api/v1/payments/create", json={"order_id": order_id, "payment_method": "UPI"}, headers=customer_auth_headers
    )
    tx_ref = create_pay.json()["data"]["transaction_reference"]

    webhook_payload = {
        "event": "payment.captured",
        "order_id": order_id,
        "transaction_reference": tx_ref,
        "amount": 320.00,
        "status": "SUCCESS",
        "signature": "test_wh_sig_12345",
    }

    # 1. First webhook call
    wh_resp1 = client.post("/api/v1/payments/webhook", json=webhook_payload)
    assert wh_resp1.status_code == 200
    assert wh_resp1.json()["data"]["status"] == "success"

    # 2. Repeated webhook call with same event/transaction_reference
    wh_resp2 = client.post("/api/v1/payments/webhook", json=webhook_payload)
    assert wh_resp2.status_code == 200
    assert wh_resp2.json()["data"]["status"] == "ignored"
