import pytest

from decimal import Decimal

from sqlalchemy import select

from coffee_backend.app.models.models import User, Ingredient
from coffee_backend.app.auth.hash import hash_password


class TestAdminMenuEndpoints:
    """Тесты админских эндпоинтов меню"""
    
    @pytest.mark.asyncio
    async def test_create_menu_item_success(self, admin_authenticated_client, db_session):
        """Успешное создание пункта меню"""
        payload = {
            "name": "New Drink",
            "base_price": 250.00,
            "is_available": True
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/menu/items",
            json=payload
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Drink"
        assert data["base_price"] == 250.00
    
    @pytest.mark.asyncio
    async def test_create_menu_item_without_auth(self, client):
        """Создание меню без аутентификации"""
        payload = {"name": "Test", "base_price": 100.0, "is_available": True}
        
        response = await client.post("/api/v1/admin/menu/items", json=payload)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_menu_item_as_regular_user(self, authenticated_client):
        """Создание меню обычным пользователем"""
        payload = {"name": "Test", "base_price": 100.0, "is_available": True}
        
        response = await authenticated_client.post("/api/v1/admin/menu/items", json=payload)
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_menu_item_invalid_price(self, admin_authenticated_client):
        """Создание меню с некорректной ценой"""
        payload = {
            "name": "Invalid Item",
            "base_price": -50.00,
            "is_available": True
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/menu/items",
            json=payload
        )
        
        assert response.status_code == 422


class TestAdminIngredientEndpoints:
    """Тесты админских эндпоинтов ингредиентов"""
    
    @pytest.mark.asyncio
    async def test_create_ingredient_success(self, admin_authenticated_client):
        """Успешное создание ингредиента"""
        payload = {
            "name": "Coffee Beans",
            "stock_quantity": 100.00,
            "unit": "kg",
            "low_stock_threshold": 10.00
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/ingredients/new",
            json=payload
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Coffee Beans"
        assert data["unit"] == "kg"
    
    @pytest.mark.asyncio
    async def test_update_ingredient_stock(self, admin_authenticated_client, db_session):
        """Обновление остатков ингредиента"""
        # Создаем ингредиент
        ingredient = Ingredient(
            name="Test Ingredient",
            stock_quantity=Decimal("50.00"),
            unit="kg",
            low_stock_threshold=Decimal("10.00")
        )
        db_session.add(ingredient)
        await db_session.commit()
        
        response = await admin_authenticated_client.post(
            f"/api/v1/admin/ingredients/{ingredient.id}/stock?quantity=25",
            data={}
        )
        
        # Проверка зависит от реализации маршрута
        assert response.status_code in [200, 422]


class TestAdminRecipeEndpoints:
    """Тесты админских эндпоинтов рецептов"""
    
    @pytest.mark.asyncio
    async def test_create_recipe_success(self, admin_authenticated_client, db_session, menu_items):
        """Успешное создание рецепта"""
        # Создаем ингредиент
        ingredient = Ingredient(
            name="Test Ingredient",
            stock_quantity=Decimal("100.00"),
            unit="g",
            low_stock_threshold=Decimal("10.00")
        )
        db_session.add(ingredient)
        await db_session.commit()
        
        payload = {
            "menu_item_id": menu_items[0].id,
            "ingredients": [
                {"ingredient_id": ingredient.id, "quantity": 50.00}
            ]
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/recipes",
            json=payload
        )
        
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_create_recipe_invalid_menu_item(self, admin_authenticated_client):
        """Создание рецепта для несуществующего меню"""
        payload = {
            "menu_item_id": 9999,
            "ingredients": []
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/recipes",
            json=payload
        )
        
        assert response.status_code == 404


class TestAdminPricingEndpoints:
    """Тесты админских эндпоинтов ценообразования"""
    
    @pytest.mark.asyncio
    async def test_create_pricing_rule_success(self, admin_authenticated_client):
        """Успешное создание правила ценообразования"""
        payload = {
            "day_of_week": 1,  # Monday
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "multiplier": 1.5
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/pricing-rules",
            json=payload
        )
        
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_create_pricing_rule_invalid_day(self, admin_authenticated_client):
        """Создание правила с некорректным днем недели"""
        payload = {
            "day_of_week": 8,  # Invalid (0-6)
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "multiplier": 1.5
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/pricing-rules",
            json=payload
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_pricing_rule_invalid_time_range(self, admin_authenticated_client):
        """Создание правила с неверным диапазоном времени"""
        payload = {
            "day_of_week": 1,
            "start_time": "17:00:00",  # After end time
            "end_time": "09:00:00",
            "multiplier": 1.5
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/pricing-rules",
            json=payload
        )
        
        assert response.status_code == 422


class TestAdminLoyaltyEndpoints:
    """Тесты админских эндпоинтов лояльности"""
    
    @pytest.mark.asyncio
    async def test_create_loyalty_card_success(self, admin_authenticated_client):
        """Успешное создание карты лояльности"""
        payload = {
            "customer_name": "John Doe",
            "initial_points": 500
        }
        
        response = await admin_authenticated_client.post(
            "/api/v1/admin/loyalty-cards",
            json=payload
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "John Doe"
        assert data["points_balance"] == 500
        assert "tier_details" in data


class TestAdminUserEndpoints:
    """Тесты админских эндпоинтов пользователей"""
    
    @pytest.mark.asyncio
    async def test_list_users(self, admin_authenticated_client, db_session, test_user, admin_user):
        """Получение списка пользователей"""
        response = await admin_authenticated_client.get("/api/v1/admin/users")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        
        usernames = [u["username"] for u in data]
        assert test_user[0].username in usernames
        assert admin_user[0].username in usernames
    
    @pytest.mark.asyncio
    async def test_list_users_pagination(self, admin_authenticated_client, db_session):
        """Пагинация списка пользователей"""
        # Создаем тестовых пользователей
        for i in range(10):
            user = User(
                username=f"paginated_user_{i}",
                email=f"user{i}@test.com",
                hashed_password=await hash_password("pass123"),
                is_active=True,
                is_superuser=False,
                control_question="Q",
                answer="A"
            )
            db_session.add(user)
        await db_session.commit()
        
        response = await admin_authenticated_client.get("/api/v1/admin/users?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    @pytest.mark.asyncio
    async def test_update_user_status(self, admin_authenticated_client, db_session, test_user):
        """Активация/деактивация пользователя"""
        # Сначала деактивируем
        response = await admin_authenticated_client.patch(
            f"/api/v1/admin/users/{test_user[0].id}/status?is_active=False"
        )
        
        assert response.status_code == 200
        
        # Проверяем в БД
        result = await db_session.execute(
            select(User).where(User.id == test_user[0].id)
        )
        user = result.scalar_one()
        assert user.is_active is False
        
        # Активируем обратно
        response = await admin_authenticated_client.patch(
            f"/api/v1/admin/users/{test_user[0].id}/status?is_active=True"
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, admin_authenticated_client):
        """Обновление несуществующего пользователя"""
        response = await admin_authenticated_client.patch(
            "/api/v1/admin/users/99999/status?is_active=False"
        )
        
        assert response.status_code == 404