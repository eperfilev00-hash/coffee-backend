import pytest
from datetime import datetime, timezone, timedelta

from coffee_backend.app.models.models import (
    User, Session, LoyaltyCard
)
from coffee_backend.app.auth.hash import hash_password

class TestLoyaltyEndpoints:
    """Тесты программы лояльности"""
    
    @pytest.mark.asyncio
    async def test_get_my_loyalty_card(self, authenticated_client, test_user):
        """Получение своей карты лояльности"""
        response = await authenticated_client.get("/api/v1/loyalty/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == test_user[1].id
        assert data["customer_name"] == test_user[0].username
        assert "tier_details" in data
    
    @pytest.mark.asyncio
    async def test_get_loyalty_card_by_id(self, authenticated_client, test_user):
        """Получение карты лояльности по ID"""
        response = await authenticated_client.get(f"/api/v1/loyalty/cards/{test_user[1].id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == test_user[1].id
    
    @pytest.mark.asyncio
    async def test_redeem_points_success(self, authenticated_client, test_user):
        """Списание баллов лояльности"""
        response = await authenticated_client.post(
            "/api/v1/loyalty/redeem",
            json={"card_id": test_user[1].id, "points": 50}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["redeemed_points"] == 50
        assert data["remaining_balance"] == 50
    
    @pytest.mark.asyncio
    async def test_redeem_more_than_balance(self, authenticated_client, test_user):
        """Списание баллов сверх баланса"""
        response = await authenticated_client.post(
            "/api/v1/loyalty/redeem",
            json={"card_id": test_user[1].id, "points": 500}
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_redeem_zero_points(self, authenticated_client, test_user):
        """Списание нулевого количества баллов"""
        response = await authenticated_client.post(
            "/api/v1/loyalty/redeem",
            json={"card_id": test_user[1].id, "points": 0}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_redeem_negative_points(self, authenticated_client, test_user):
        """Списание отрицательных баллов"""
        response = await authenticated_client.post(
            "/api/v1/loyalty/redeem",
            json={"card_id": test_user[1].id, "points": -10}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_redeem_for_other_user_forbidden(self, client, db_session, test_user):
        """Попытка списать баллы чужой карты без прав админа"""
        # Создаем другого пользователя
        other_user = User(
            username="other_user",
            email="other@example.com",
            hashed_password=await hash_password("pass123"),
            is_active=True,
            is_superuser=False,
            control_question="Q",
            answer="A"
        )
        db_session.add(other_user)
        await db_session.flush()
        
        other_card = LoyaltyCard(
            user_id=other_user.id,
            customer_name="other",
            points_balance=1000,
            tier="gold"
        )
        db_session.add(other_card)
        await db_session.commit()
        
        # Создаем сессию для первого пользователя
        session = Session(
            session_id="test-session-id-12345",
            user_id=test_user[0].id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True
        )
        db_session.add(session)
        await db_session.commit()
        
        client.cookies.set("session_id", "test-session-id-12345")
        
        response = await client.post(
            "/api/v1/loyalty/redeem",
            json={"card_id": other_card.id, "points": 100}
        )
        
        assert response.status_code == 403