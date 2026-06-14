import pytest
from coffee_backend.app.schemas import OrderItemRequest
class TestOrderEndpoints:
    """Тесты эндпоинтов заказов"""
    
    @pytest.mark.asyncio
    async def test_create_order_success(
        self, authenticated_client, db_session, test_user, menu_items
    ):
        """Успешное создание заказа"""
        order_data = {
            "items": [
                {"menu_item_id": menu_items[0].id, "quantity": 2},
                {"menu_item_id": menu_items[1].id, "quantity": 1}
            ],
            "card_id": test_user[1].id
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/orders",
            json=order_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "total_price" in data
        assert "final_price" in data
        assert "items" in data
        assert len(data["items"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_order_without_auth(self, client, menu_items):
        """Создание заказа без аутентификации"""
        order_data = {
            "items": [
                {"menu_item_id": menu_items[0].id, "quantity": 1}
            ]
        }
        
        response = await client.post("/api/v1/orders/orders", json=order_data)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_item(self, authenticated_client, test_user):
        """Создание заказа с несуществующим пунктом меню"""
        order_data = {
            "items": [
                {"menu_item_id": 9999, "quantity": 1}
            ],
            "card_id": test_user[1].id
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/orders",
            json=order_data
        )
        
        assert response.status_code in [400, 404, 422]
    
    @pytest.mark.asyncio
    async def test_create_order_zero_quantity(self, authenticated_client, test_user, menu_items):
        """Создание заказа с нулевым количеством"""
        order_data = {
            "items": [
                {"menu_item_id": menu_items[0].id, "quantity": 0}
            ],
            "card_id": test_user[1].id
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/orders",
            json=order_data
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_order_negative_quantity(self, authenticated_client, test_user, menu_items):
        """Создание заказа с отрицательным количеством"""
        order_data = {
            "items": [
                {"menu_item_id": menu_items[0].id, "quantity": -1}
            ],
            "card_id": test_user[1].id
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/orders",
            json=order_data
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_order_by_id(self, authenticated_client, db_session, test_user, menu_items):
        """Получение заказа по ID"""
        # Создаем заказ
        from coffee_backend.app.services.order_services import create_order
        from coffee_backend.app.schemas import OrderCreateRequest
        
        order_data = OrderCreateRequest(
        items=[
            OrderItemRequest(menu_item_id=menu_items[0].id, quantity=1)
        ],
        card_id=test_user[1].id
    )
        
        async with db_session.begin():
            order_response = await create_order(db_session, order_data, test_user[0])
        
        order_id = order_response.id
        
        response = await authenticated_client.get(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self, authenticated_client):
        """Получение несуществующего заказа"""
        response = await authenticated_client.get("/api/v1/orders/99999")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_user_orders(self, authenticated_client, db_session, test_user, menu_items):
        """Получение истории заказов пользователя"""
        # Создаем несколько заказов
        for _ in range(3):
            order_data = {
                "items": [{"menu_item_id": menu_items[0].id, "quantity": 1}],
                "card_id": test_user[1].id
            }
            await authenticated_client.post("/api/v1/orders/orders", json=order_data)
        
        response = await authenticated_client.get("/api/v1/orders")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3