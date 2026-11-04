def test_list_kitchens(client):
    response = client.get("/api/v1/kitchens")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["meta"]["total_count"] >= 2
    assert any(k["name"] == "Indiranagar Cloud Kitchen" for k in data["items"])


def test_get_kitchen_detail(client):
    response = client.get("/api/v1/kitchens/1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["kitchen_id"] == 1
    assert data["name"] == "Indiranagar Cloud Kitchen"


def test_get_invalid_kitchen_id(client):
    response = client.get("/api/v1/kitchens/99999")
    assert response.status_code == 404


def test_list_categories(client):
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    categories = response.json()["data"]
    assert len(categories) >= 2
    assert any(c["slug"] == "gourmet-bowls" for c in categories)


def test_search_menu(client):
    response = client.get("/api/v1/menu?search=Butter")
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) >= 1
    assert "Butter Chicken" in items[0]["name"]


def test_get_menu_item_detail(client):
    response = client.get("/api/v1/menu/1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["menu_item_id"] == 1
    assert data["name"] == "Butter Chicken Rice Bowl"


def test_get_invalid_menu_id(client):
    response = client.get("/api/v1/menu/99999")
    assert response.status_code == 404
