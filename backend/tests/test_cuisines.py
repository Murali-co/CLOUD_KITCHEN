import pytest


def test_list_cuisines(client):
    """Verify listing all active cuisines ordered by display_order."""
    response = client.get("/api/v1/cuisines")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    cuisines = res_data["data"]
    assert len(cuisines) == 15

    # Check first cuisine is South Indian with display_order 1
    assert cuisines[0]["cuisine_id"] == 1
    assert cuisines[0]["cuisine_name"] == "South Indian"
    assert cuisines[0]["cuisine_slug"] == "south-indian"
    assert cuisines[0]["is_active"] is True
    assert cuisines[0]["display_order"] == 1

    # Check Italian is cuisine 4
    italian = next((c for c in cuisines if c["cuisine_slug"] == "italian"), None)
    assert italian is not None
    assert italian["cuisine_name"] == "Italian"
    assert italian["cuisine_id"] == 4


def test_get_cuisine_by_id(client):
    """Verify getting a single cuisine with its associated menu items."""
    # Test valid cuisine ID: 4 (Italian)
    response = client.get("/api/v1/cuisines/4")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["cuisine_id"] == 4
    assert data["cuisine_name"] == "Italian"
    assert data["cuisine_slug"] == "italian"
    assert "item_count" in data
    assert data["item_count"] >= 1


def test_get_cuisine_by_id_not_found(client):
    """Verify 404 response for invalid cuisine ID."""
    response = client.get("/api/v1/cuisines/9999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_get_cuisine_by_slug(client):
    """Verify getting cuisine detail by unique slug."""
    response = client.get("/api/v1/cuisines/slug/hyderabadi")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["cuisine_id"] == 13
    assert data["cuisine_name"] == "Hyderabadi"
    assert "item_count" in data
    assert data["item_count"] >= 1


def test_get_cuisine_by_slug_not_found(client):
    """Verify 404 response for invalid cuisine slug."""
    response = client.get("/api/v1/cuisines/slug/unknown-cuisine-slug")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_menu_filter_by_cuisine_id(client):
    """Verify menu items can be filtered specifically by cuisine_id."""
    # Filter for North Indian (ID 2)
    response = client.get("/api/v1/menu?cuisine_id=2")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    dishes = res_data["data"]["items"]
    assert len(dishes) > 0
    for dish in dishes:
        assert dish["cuisine_id"] == 2

    # Filter for Italian (ID 4)
    response_it = client.get("/api/v1/menu?cuisine_id=4")
    assert response_it.status_code == 200
    dishes_it = response_it.json()["data"]["items"]
    assert len(dishes_it) > 0
    for dish in dishes_it:
        assert dish["cuisine_id"] == 4
