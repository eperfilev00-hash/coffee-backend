import pytest
from decimal import Decimal
from unittest.mock import patch
from datetime import time

from coffee_backend.app.schemas import OrderCreateRequest, OrderItemRequest
from coffee_backend.app.services.order_services import create_order
from coffee_backend.app.services.pricing import get_current_multiplier
from tests.factories import (
    create_ingredient,
    create_menu_item,
    create_recipe,
    seed_loyalty_tiers,
    create_loyalty_card,
    create_pricing_rule,
)


@pytest.mark.asyncio
async def test_create_order_service_calculates_price(db_session):
    ingredient = await create_ingredient(db_session, stock_quantity=Decimal("100"))
    item = await create_menu_item(db_session, base_price=Decimal("50.00"))
    await create_recipe(db_session, item.id, ingredient.id, Decimal("1"))

    order_data = OrderCreateRequest(
        items=[OrderItemRequest(menu_item_id=item.id, quantity=2)],
    )
    result = await create_order(db_session, order_data)

    assert result.total_price == 100.0
    assert result.status == "confirmed"
    assert result.items[0].total_line == 100.0


@pytest.mark.asyncio
async def test_create_order_service_reserves_stock(db_session):
    ingredient = await create_ingredient(db_session, stock_quantity=Decimal("10"))
    item = await create_menu_item(db_session, base_price=Decimal("10.00"))
    await create_recipe(db_session, item.id, ingredient.id, Decimal("3"))

    order_data = OrderCreateRequest(
        items=[OrderItemRequest(menu_item_id=item.id, quantity=2)],
    )
    await create_order(db_session, order_data)
    await db_session.flush()  # принудительно отправляем UPDATE в БД

    # Перечитываем состояние (все еще внутри тестовой транзакции)
    from sqlalchemy import select
    from coffee_backend.app.models.models import Ingredient
    result = await db_session.execute(select(Ingredient).where(Ingredient.id == ingredient.id))
    updated = result.scalar_one()
    assert updated.stock_quantity == Decimal("4")  # 10 - (3 * 2)


@pytest.mark.asyncio
async def test_get_current_multiplier_applies_rule(db_session):
    await create_pricing_rule(
        db_session,
        day_of_week=0,
        start_time=time(0, 0),
        end_time=time(23, 59),
        multiplier=Decimal("1.5"),
    )
    # Мокаем datetime, чтобы правило гарантированно подошло
    with patch("coffee_backend.app.services.pricing.datetime") as mock_dt:
        mock_dt.now.return_value.weekday.return_value = 0
        mock_dt.now.return_value.time.return_value = time(12, 0)

        mult = await get_current_multiplier(db_session)
        assert mult == Decimal("1.5")

@pytest.mark.asyncio
async def test_insufficient_stock_returns_409(client, db_session):
    ingredient = await create_ingredient(db_session, stock_quantity=Decimal("1"))
    item = await create_menu_item(db_session, base_price=Decimal("10.00"))
    await create_recipe(db_session, item.id, ingredient.id, Decimal("999"))

    payload = {
        "items": [{"menu_item_id": item.id, "quantity": 1}],
    }
    response = await client.post("/api/v1/orders", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_STOCK"
    assert "missing_items" in data["error"]