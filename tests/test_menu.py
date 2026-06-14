import pytest
from decimal import Decimal

from coffee_backend.app.models.models import MenuItem

class TestMenuEndpoints:
    """Тесты эндпоинтов меню"""
    
    @pytest.mark.asyncio
    async def test_get_menu_empty(self, client, db_session):
        """Получение пустого меню"""
        response = await client.get("/api/v1/menu")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_get_menu_with_items(self, client, db_session, menu_items):
        """Получение меню с пунктами"""
        response = await client.get("/api/v1/menu")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        for item in data:
            assert "id" in item
            assert "name" in item
            assert "base_price" in item
            assert "current_price" in item
            assert item["is_available"] is True
    
    @pytest.mark.asyncio
    async def test_get_menu_excludes_unavailable(self, client, db_session):
        """Меню не включает недоступные пункты"""
        unavailable = MenuItem(
            name="Unavailable Item",
            base_price=Decimal("150.00"),
            is_available=False
        )
        db_session.add(unavailable)
        await db_session.commit()
        
        response = await client.get("/api/v1/menu")
        
        assert response.status_code == 200
        data = response.json()
        assert not any(item["name"] == "Unavailable Item" for item in data)
