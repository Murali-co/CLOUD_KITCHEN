def test_get_customer_profile(client, customer_auth_headers):
    response = client.get("/api/v1/customer/profile", headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "customer1@test.com"
    assert data["loyalty_points"] == 100


def test_update_customer_profile(client, customer_auth_headers):
    payload = {
        "first_name": "UpdatedFirst",
        "last_name": "UpdatedLast",
        "phone_number": "+919800999999",
        "dietary_preference": "VEGAN",
    }
    response = client.put("/api/v1/customer/profile", json=payload, headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["first_name"] == "UpdatedFirst"
    assert data["phone_number"] == "+919800999999"
    assert data["dietary_preference"] == "VEGAN"


def test_list_addresses(client, customer_auth_headers):
    response = client.get("/api/v1/customer/addresses", headers=customer_auth_headers)
    assert response.status_code == 200
    addresses = response.json()["data"]
    assert len(addresses) >= 1
    assert addresses[0]["address_label"] == "Home"


def test_create_address(client, customer_auth_headers):
    payload = {
        "address_label": "Gym",
        "recipient_name": "Test Customer",
        "recipient_phone": "+919800000001",
        "address_line1": "Fitness Center, Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
        "is_default": False,
    }
    response = client.post("/api/v1/customer/addresses", json=payload, headers=customer_auth_headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["address_label"] == "Gym"


def test_unauthorized_address_access(client, other_customer_auth_headers):
    # Customer 2 attempts to edit Customer 1's address (address_id=1)
    payload = {"address_label": "Hacked Label"}
    response = client.put("/api/v1/customer/addresses/1", json=payload, headers=other_customer_auth_headers)
    assert response.status_code == 404  # Address isolation enforced
