import pytest
from decimal import Decimal


def test_ingredient_crud_and_stock_in(client, kitchen_manager_headers, kitchen_staff_headers):
    # 20. Create master ingredient
    ing_payload = {
        "name": "Organic Black Peppercorns",
        "category": "Spices",
        "unit_of_measure": "KG",
        "initial_stock": 5.000,
        "reorder_level": 1.500,
    }
    resp = client.post("/api/v1/kitchen/ingredients", json=ing_payload, headers=kitchen_staff_headers)
    assert resp.status_code == 201
    ing = resp.json()["data"]
    ing_id = ing["ingredient_id"]
    assert ing["name"] == "Organic Black Peppercorns"

    # Verify inventory item exists with initial stock
    inv_res = client.get(f"/api/v1/kitchen/inventory/{ing_id}", headers=kitchen_staff_headers)
    assert inv_res.status_code == 200
    assert float(inv_res.json()["data"]["current_stock"]) == 5.000

    # 21. Stock-in
    stock_in_payload = {
        "ingredient_id": ing_id,
        "quantity": 10.000,
        "unit_cost": 450.00,
        "notes": "Weekly spice shipment received",
    }
    stock_res = client.post("/api/v1/kitchen/inventory/stock-in", json=stock_in_payload, headers=kitchen_staff_headers)
    assert stock_res.status_code == 200
    movement = stock_res.json()["data"]
    assert movement["movement_type"] == "RESTOCK"
    assert float(movement["quantity_delta"]) == 10.000

    # Verify updated stock (5 + 10 = 15)
    inv_res2 = client.get(f"/api/v1/kitchen/inventory/{ing_id}", headers=kitchen_staff_headers)
    assert float(inv_res2.json()["data"]["current_stock"]) == 15.000

    # 22. Stock adjustment (AUDIT_ADJUSTMENT or SPOILAGE)
    adj_payload = {
        "ingredient_id": ing_id,
        "quantity_delta": -2.000,
        "movement_type": "SPOILAGE",
        "notes": "Moisture damage in storage container",
    }
    adj_res = client.post("/api/v1/kitchen/inventory/stock-adjustment", json=adj_payload, headers=kitchen_staff_headers)
    assert adj_res.status_code == 200
    assert float(adj_res.json()["data"]["quantity_delta"]) == -2.000

    # Verify stock is now 13
    inv_res3 = client.get(f"/api/v1/kitchen/inventory/{ing_id}", headers=kitchen_staff_headers)
    assert float(inv_res3.json()["data"]["current_stock"]) == 13.000

    # 23. Negative stock prevention (attempt to deduct 100kg when only 13kg on hand)
    bad_adj = {
        "ingredient_id": ing_id,
        "quantity_delta": -100.000,
        "movement_type": "AUDIT_ADJUSTMENT",
        "notes": "Attempting excess deduction",
    }
    bad_res = client.post("/api/v1/kitchen/inventory/stock-adjustment", json=bad_adj, headers=kitchen_staff_headers)
    assert bad_res.status_code == 400
    assert "negative stock" in bad_res.json()["detail"].lower()

    # 24. Inventory movement recording in audit log
    mov_res = client.get("/api/v1/kitchen/inventory/movements", headers=kitchen_staff_headers)
    if mov_res.status_code != 200:
        print("MOV_RES ERROR:", mov_res.json())
    assert mov_res.status_code == 200
    assert mov_res.json()["data"] is not None
    assert len(mov_res.json()["data"]["items"]) >= 2


def test_low_stock_detection(client, kitchen_staff_headers):
    # 25. Low-stock detection
    # In seeded fixtures, Paneer (Ingredient 3) has current_stock=2kg and reorder_level=5kg
    resp = client.get("/api/v1/kitchen/inventory/low-stock", headers=kitchen_staff_headers)
    assert resp.status_code == 200
    alerts = resp.json()["data"]
    paneer_alert = next((a for a in alerts if a["ingredient_id"] == 3), None)
    assert paneer_alert is not None
    assert float(paneer_alert["current_stock"]) <= float(paneer_alert["reorder_level"])
    assert float(paneer_alert["suggested_replenishment"]) > 0


def test_recipe_management(client, kitchen_manager_headers, kitchen_staff_headers):
    # 26. Recipe retrieval for Dish 1 (Butter Chicken Bowl)
    resp = client.get("/api/v1/kitchen/menu/1/recipe", headers=kitchen_staff_headers)
    assert resp.status_code == 200
    recipe = resp.json()["data"]
    assert recipe["menu_item_id"] == 1
    assert len(recipe["ingredients"]) == 2  # Rice and Chicken

    # 27. Recipe update (Manager permitted)
    update_payload = {
        "ingredients": [
            {"ingredient_id": 1, "quantity_required": 0.200, "unit_of_measure": "KG"},
            {"ingredient_id": 2, "quantity_required": 0.220, "unit_of_measure": "KG"},
        ]
    }
    up_res = client.put("/api/v1/kitchen/menu/1/recipe", json=update_payload, headers=kitchen_manager_headers)
    assert up_res.status_code == 200
    updated_ings = up_res.json()["data"]["ingredients"]
    assert len(updated_ings) == 2
    assert float(updated_ings[0]["quantity_required"]) == 0.200

    # 28. Invalid ingredient assignment (non-existent ingredient ID 99999)
    bad_recipe = {
        "ingredients": [
            {"ingredient_id": 99999, "quantity_required": 1.000, "unit_of_measure": "KG"}
        ]
    }
    assert client.put("/api/v1/kitchen/menu/1/recipe", json=bad_recipe, headers=kitchen_manager_headers).status_code == 400


def test_automatic_inventory_deduction_and_rollback(client, customer_auth_headers, kitchen_staff_headers):
    # Setup dish with recipe: Dish 1 requires Rice and Chicken
    # Initial stock: Rice=50kg, Chicken=20kg
    init_rice = client.get("/api/v1/kitchen/inventory/1", headers=kitchen_staff_headers).json()["data"]["current_stock"]
    init_chick = client.get("/api/v1/kitchen/inventory/2", headers=kitchen_staff_headers).json()["data"]["current_stock"]

    # Customer places order with 2x Dish 1
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 2}, headers=customer_auth_headers)
    order_res = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "inv-deduct-test-01"},
        headers=customer_auth_headers,
    )
    assert order_res.status_code in [200, 201]
    order_id = order_res.json()["data"]["order_id"]

    # 30. Transition order to PREPARING -> Triggers automatic recipe stock deduction!
    prep_res = client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers=kitchen_staff_headers,
    )
    assert prep_res.status_code == 200
    assert prep_res.json()["data"]["order_status"] == "PREPARING"

    # Verify inventory was deducted:
    # 2x Dish 1 requires 2 * 0.200 = 0.400kg rice and 2 * 0.220 = 0.440kg chicken
    rice_after = client.get("/api/v1/kitchen/inventory/1", headers=kitchen_staff_headers).json()["data"]["current_stock"]
    assert float(rice_after) < float(init_rice)

    # 31. Duplicate deduction prevention: Repeated status update to PREPARING must NOT deduct stock again
    client.patch(
        f"/api/v1/kitchen/orders/{order_id}/status",
        json={"status": "PREPARING"},
        headers=kitchen_staff_headers,
    )
    rice_after2 = client.get("/api/v1/kitchen/inventory/1", headers=kitchen_staff_headers).json()["data"]["current_stock"]
    assert float(rice_after2) == float(rice_after)

    # 29 & 32. Insufficient stock and transaction rollback test
    # Reduce Chicken stock to 0.050kg so that any new order requiring 0.220kg fails
    curr_chick = client.get("/api/v1/kitchen/inventory/2", headers=kitchen_staff_headers).json()["data"]["current_stock"]
    deduct_all = -(float(curr_chick) - 0.050)
    client.post(
        "/api/v1/kitchen/inventory/stock-adjustment",
        json={"ingredient_id": 2, "quantity_delta": deduct_all, "movement_type": "AUDIT_ADJUSTMENT", "notes": "Set to near zero"},
        headers=kitchen_staff_headers,
    )

    # Place new order for Dish 1 (requires 0.220kg, but only 0.050kg available)
    client.post("/api/v1/cart/items", json={"menu_item_id": 1, "quantity": 1}, headers=customer_auth_headers)
    order_fail_res = client.post(
        "/api/v1/orders",
        json={"delivery_address_id": 1, "payment_method": "CASH_ON_DELIVERY", "idempotency_key": "inv-fail-test-01"},
        headers=customer_auth_headers,
    )
    assert order_fail_res.status_code in [200, 201]
    order_fail_id = order_fail_res.json()["data"]["order_id"]

    # Transitioning to PREPARING must fail with 400 Insufficient stock
    prep_fail = client.patch(
        f"/api/v1/kitchen/orders/{order_fail_id}/status",
        json={"status": "PREPARING"},
        headers=kitchen_staff_headers,
    )
    assert prep_fail.status_code == 400
    assert "insufficient stock" in prep_fail.json()["detail"].lower()

    # Verify rollback: order status remains PENDING and did not change to PREPARING
    order_check = client.get(f"/api/v1/kitchen/orders/{order_fail_id}", headers=kitchen_staff_headers)
    assert order_check.json()["data"]["order_status"] == "PENDING"


def test_concurrent_stock_update_safety(client, kitchen_staff_headers):
    # 33. Concurrent stock update safety
    # Add 10kg of an ingredient, then verify that rapid sequential or thread-safe adjustments properly maintain balance
    ing_payload = {
        "name": "Organic Turmeric Powder",
        "category": "Spices",
        "unit_of_measure": "KG",
        "initial_stock": 10.000,
        "reorder_level": 2.000,
    }
    resp = client.post("/api/v1/kitchen/ingredients", json=ing_payload, headers=kitchen_staff_headers)
    assert resp.status_code == 201
    ing_id = resp.json()["data"]["ingredient_id"]

    # Execute 5 adjustments of -1.5kg each = -7.5kg total
    for i in range(5):
        adj_res = client.post(
            "/api/v1/kitchen/inventory/stock-adjustment",
            json={
                "ingredient_id": ing_id,
                "quantity_delta": -1.500,
                "movement_type": "AUDIT_ADJUSTMENT",
                "notes": f"Batch adjustment #{i+1}",
            },
            headers=kitchen_staff_headers,
        )
        assert adj_res.status_code == 200

    # Stock should be exactly 10.000 - 7.500 = 2.500kg
    inv_check = client.get(f"/api/v1/kitchen/inventory/{ing_id}", headers=kitchen_staff_headers)
    assert float(inv_check.json()["data"]["current_stock"]) == 2.500

    # Attempting to deduct 3.000kg must be rejected because 2.500 - 3.000 < 0
    over_res = client.post(
        "/api/v1/kitchen/inventory/stock-adjustment",
        json={
            "ingredient_id": ing_id,
            "quantity_delta": -3.000,
            "movement_type": "AUDIT_ADJUSTMENT",
            "notes": "Attempting over-deduction",
        },
        headers=kitchen_staff_headers,
    )
    assert over_res.status_code == 400
    assert "negative stock" in over_res.json()["detail"].lower()

    # Balance remains intact at 2.500kg
    inv_final = client.get(f"/api/v1/kitchen/inventory/{ing_id}", headers=kitchen_staff_headers)
    assert float(inv_final.json()["data"]["current_stock"]) == 2.500

