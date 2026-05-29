import pytest
from decimal import Decimal
from tests.factories import (
    create_ingredient,
    create_menu_item,
    create_recipe,
    seed_loyalty_tiers,
    create_loyalty_card,
)


@pytest.mark.asyncio
async def test_create_order_success(client, db_session):
    ingredient = await create_ingredient(db_session, stock_quantity=Decimal("500"))
    item = await create_menu_item(db_session, base_price=Decimal("10.00"))
    await create_recipe(db_session, item.id, ingredient.id, Decimal("5"))

    payload = {
        "items": [{"menu_item_id": item.id, "quantity": 2}],
        "card_id": None,
        "redeem_points": 0,
    }
    response = await client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["total_price"] == 20.0
    assert data["status"] == "confirmed"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_create_order_duplicate_items_returns_422(client, db_session):
    item = await create_menu_item(db_session)
    payload = {
        "items": [
            {"menu_item_id": item.id, "quantity": 1},
            {"menu_item_id": item.id, "quantity": 1},
        ]
    }
    response = await client.post("/api/v1/orders", json=payload)
    assert response.status_code == 422
    assert "Дубликат" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_order_with_loyalty_card(client, db_session):
    await seed_loyalty_tiers(db_session)
    ingredient = await create_ingredient(db_session, stock_quantity=Decimal("500"))
    item = await create_menu_item(db_session, base_price=Decimal("100.00"))
    await create_recipe(db_session, item.id, ingredient.id, Decimal("1"))

    card = await create_loyalty_card(db_session, points_balance=50, tier="bronze")

    payload = {
        "items": [{"menu_item_id": item.id, "quantity": 1}],
        "card_id": card.id,
        "redeem_points": 10,
    }
    response = await client.post("/api/v1/orders", json=payload)
    assert response.status_code == 201
    data = response.json()

    # 100 - скидка 10% (для bronze 0) - 10 баллов = 90.00
    assert data["final_price"] == 90.0
    assert data["discount_applied"] == 0.0
    assert data["points_earned"] > 0


@pytest.mark.asyncio
async def test_get_order_not_found(client):
    response = await client.get("/api/v1/orders/99999")
    assert response.status_code == 404
    assert "не найден" in response.json()["detail"]