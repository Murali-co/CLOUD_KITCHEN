import pytest


def test_register_success(client):
    payload = {
        "full_name": "New Customer",
        "email": "newcustomer@test.com",
        "phone_number": "+919811122299",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newcustomer@test.com"
    assert data["data"]["role"] == "CUSTOMER"
    assert "password_hash" not in data["data"]


def test_register_invalid_email(client):
    payload = {
        "full_name": "Bad Email",
        "email": "not-an-email",
        "phone_number": "+919811122298",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_weak_password(client):
    payload = {
        "full_name": "Weak Pass",
        "email": "weak@test.com",
        "phone_number": "+919811122297",
        "password": "weak",
        "confirm_password": "weak",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_duplicate_email(client):
    payload = {
        "full_name": "Duplicate User",
        "email": "customer1@test.com",  # Already in conftest seed
        "phone_number": "+919811122296",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_register_duplicate_phone(client):
    payload = {
        "full_name": "Duplicate Phone User",
        "email": "unique@test.com",
        "phone_number": "+919800000001",  # Already in conftest seed
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "phone number already exists" in response.json()["detail"]


def test_login_success(client):
    payload = {
        "email": "customer1@test.com",
        "password": "Password@123",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "customer1@test.com"


def test_login_invalid_password(client):
    payload = {
        "email": "customer1@test.com",
        "password": "WrongPassword999",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_inactive_user(client):
    payload = {
        "email": "inactive@test.com",
        "password": "Password@123",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_get_current_user_me(client, customer_auth_headers):
    response = client.get("/api/v1/auth/me", headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "customer1@test.com"
    assert data["role"] == "CUSTOMER"


def test_get_current_user_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_change_password_success(client, customer_auth_headers):
    payload = {
        "current_password": "Password@123",
        "new_password": "NewPassword@456",
        "confirm_password": "NewPassword@456",
    }
    response = client.post("/api/v1/auth/change-password", json=payload, headers=customer_auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Test login with new password
    login_resp = client.post("/api/v1/auth/login", json={"email": "customer1@test.com", "password": "NewPassword@456"})
    assert login_resp.status_code == 200


def test_logout(client, customer_auth_headers):
    response = client.post("/api/v1/auth/logout", headers=customer_auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["revoked"] is True
