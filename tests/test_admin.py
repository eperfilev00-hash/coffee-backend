import pytest


@pytest.mark.asyncio
async def test_create_menu_item(client):
    payload = {"name": "Cappuccino", "base_price": 4.50, "is_available": True}
    response = await client.post("/api/v1/admin/menu/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cappuccino"
    assert isinstance(data["id"], int)


@pytest.mark.asyncio
async def test_create_ingredient(client):
    payload = {
        "name": "Syrup",
        "stock_quantity": 200,
        "unit": "ml",
        "low_stock_threshold": 20,
    }
    response = await client.post("/api/v1/admin/ingredients/new", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Syrup"