import pytest
from app.models import Customer, DietaryPreference


def test_load_customer_profile_and_initial_preference(client, customer_auth_headers):
    """1 & 2: Load customer profile and existing dietary preference."""
    response = client.get("/api/v1/customer/profile", headers=customer_auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["email"] == "customer1@test.com"
    assert data["dietary_preference"] == "ALL"
    assert data["customer"]["dietary_preference"] == "ALL"


def test_partial_update_dietary_preference(client, customer_auth_headers):
    """3: Update dietary preference with partial payload (no first/last/phone required)."""
    payload = {"dietary_preference": "VEGAN"}
    response = client.put("/api/v1/customer/profile", json=payload, headers=customer_auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["dietary_preference"] == "VEGAN"
    assert data["customer"]["dietary_preference"] == "VEGAN"
    # Verify user names and phone are preserved
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Customer"
    assert data["phone_number"] == "+919800000001"


def test_update_to_each_supported_preference(client, customer_auth_headers):
    """4: Verify update to every supported preference in DietaryPreference enum."""
    supported_prefs = ["ALL", "VEGETARIAN", "VEGAN", "HALAL", "GLUTEN_FREE"]
    for pref in supported_prefs:
        resp = client.put("/api/v1/customer/profile", json={"dietary_preference": pref}, headers=customer_auth_headers)
        assert resp.status_code == 200, f"Failed updating to {pref}"
        assert resp.json()["data"]["dietary_preference"] == pref
        assert resp.json()["data"]["customer"]["dietary_preference"] == pref


def test_invalid_preference_handling(client, customer_auth_headers):
    """5: Verify validation error (422) on unsupported dietary preference."""
    invalid_prefs = ["INVALID", "PORK", "CARNIVORE", "JAIN", ""]
    for bad in invalid_prefs:
        resp = client.put("/api/v1/customer/profile", json={"dietary_preference": bad}, headers=customer_auth_headers)
        assert resp.status_code == 422, f"Expected 422 for {bad}, got {resp.status_code}"
        assert resp.json()["success"] is False


def test_missing_authentication_token(client):
    """6: Missing authentication token must be rejected with 401."""
    # GET profile unauthenticated
    resp_get = client.get("/api/v1/customer/profile")
    assert resp_get.status_code == 401

    # PUT profile unauthenticated
    resp_put = client.put("/api/v1/customer/profile", json={"dietary_preference": "VEGAN"})
    assert resp_put.status_code == 401


def test_unauthorized_cross_customer_update(client, customer_auth_headers, other_customer_auth_headers, db_session):
    """7: Customer 1 updating preference cannot modify Customer 2, even if customer_id injected."""
    # Check Customer 2 initial preference (VEGETARIAN)
    resp2_init = client.get("/api/v1/customer/profile", headers=other_customer_auth_headers)
    assert resp2_init.json()["data"]["dietary_preference"] == "VEGETARIAN"

    # Customer 1 attempts to update, injecting customer_id: 20 in payload
    evil_payload = {
        "customer_id": 20,
        "user_id": 20,
        "dietary_preference": "HALAL"
    }
    resp1 = client.put("/api/v1/customer/profile", json=evil_payload, headers=customer_auth_headers)
    assert resp1.status_code == 200
    assert resp1.json()["data"]["dietary_preference"] == "HALAL"
    assert resp1.json()["data"]["user_id"] == 10  # Must be customer 1

    # Verify Customer 2 remains strictly VEGETARIAN
    resp2_check = client.get("/api/v1/customer/profile", headers=other_customer_auth_headers)
    assert resp2_check.json()["data"]["dietary_preference"] == "VEGETARIAN"


def test_database_persistence_and_subsequent_get(client, customer_auth_headers, db_session):
    """8 & 9: Verify persistence directly in the database and across subsequent GET calls."""
    # Update to GLUTEN_FREE
    resp_put = client.put("/api/v1/customer/profile", json={"dietary_preference": "GLUTEN_FREE"}, headers=customer_auth_headers)
    assert resp_put.status_code == 200

    # Direct DB inspection
    db_session.expire_all()
    cust_db = db_session.query(Customer).filter(Customer.customer_id == 10).first()
    assert cust_db is not None
    # Check enum or value
    pref_db = cust_db.dietary_preference.value if hasattr(cust_db.dietary_preference, "value") else str(cust_db.dietary_preference)
    assert pref_db == "GLUTEN_FREE"

    # Subsequent GET (simulating page refresh)
    resp_get = client.get("/api/v1/customer/profile", headers=customer_auth_headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["data"]["dietary_preference"] == "GLUTEN_FREE"
    assert resp_get.json()["data"]["customer"]["dietary_preference"] == "GLUTEN_FREE"


def test_backend_error_handling_duplicate_phone(client, customer_auth_headers):
    """10: Verify backend error handling (e.g. duplicate phone collision returns 400)."""
    # Customer 1 tries to change phone to Customer 2's phone
    payload = {"phone_number": "+919800000002", "dietary_preference": "VEGAN"}
    resp = client.put("/api/v1/customer/profile", json=payload, headers=customer_auth_headers)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]
