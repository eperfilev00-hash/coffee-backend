
import pytest
from decimal import Decimal

from coffee_backend.app.models.models import MenuItem

class TestEdgeCases:
    """Тесты граничных случаев"""
    
    @pytest.mark.asyncio
    async def test_empty_username_registration(self, client):
        """Регистрация с пустым именем"""
        payload = {
            "username": "",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "control_question": "Q",
            "answer": "A"
        }
        
        response = await client.post("/api/v1/auth/registration", json=payload)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_very_long_username(self, client):
        """Регистрация с очень длинным именем"""
        payload = {
            "username": "a" * 200,
            "email": "test@example.com",
            "password": "SecurePass123!",
            "control_question": "Q",
            "answer": "A"
        }
        
        response = await client.post("/api/v1/auth/registration", json=payload)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_order_with_many_items(self, authenticated_client, db_session, test_user, menu_items):
        """Заказ с большим количеством пунктов"""
        # Создаем много пунктов меню
        for i in range(20):
            item = MenuItem(
                name=f"Item {i}",
                base_price=Decimal("100.00"),
                is_available=True
            )
            db_session.add(item)
        await db_session.commit()
        
        # Создаем заказ с 20 пунктами
        items = [{"menu_item_id": i + 1, "quantity": 1} for i in range(20)]
        order_data = {
            "items": items,
            "card_id": test_user[1].id
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/orders",
            json=order_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 20
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, authenticated_client, test_user):
        """Параллельные запросы"""
        import asyncio
        
        # Отправляем несколько параллельных запросов
        responses = await asyncio.gather(
            authenticated_client.get("/api/v1/auth/me"),
            authenticated_client.get("/api/v1/loyalty/me"),
            authenticated_client.get("/api/v1/menu"),
            return_exceptions=True
        )
        
        for response in responses:
            if isinstance(response, Exception):
                raise response
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client):
        """Некорректный JSON в запросе"""
        response = await client.post(
            "/api/v1/auth/registration",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, authenticated_client, menu_items):
        """Попытка SQL-инъекции"""
        client, test_user = authenticated_client

        order_data = {
            "items": [
                {"menu_item_id": "1; DROP TABLE users; --", "quantity": 1}
            ],
            "card_id": test_user[1].id
        }

        response = await client.post("/api/v1/orders/orders", json=order_data)

        assert response.status_code in [400, 422]
