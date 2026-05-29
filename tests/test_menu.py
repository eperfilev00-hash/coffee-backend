import pytest
from decimal import Decimal
from tests.factories import create_menu_item


@pytest.mark.asyncio
async def test_get_menu_empty(client):
    response = await client.get("/api/v1/menu")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_menu_returns_available_items(client, db_session):
    await create_menu_item(db_session, name="Espresso", base_price=Decimal("3.00"))
    await create_menu_item(db_session, name="Old Brew", base_price=Decimal("2.00"), is_available=False)

    response = await client.get("/api/v1/menu")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Espresso"
    assert data[0]["is_available"] is True