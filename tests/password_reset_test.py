import pytest
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from coffee_backend.app.models.models import User
from coffee_backend.app.auth.hash import verify_password

class TestPasswordResetEndpoints:
    """Тесты сброса пароля"""
    
    @pytest.mark.asyncio
    async def test_forgot_password(self, client, test_user):
        """Инициация сброса пароля"""
        payload = {"email": test_user[0].email}
        
        response = await client.post("/api/v1/forgot-password", json=payload)
        
        assert response.status_code == 200
        assert "Если ваш email" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, client):
        """Инициация сброса для несуществующего email"""
        payload = {"email": "nonexistent@example.com"}
        
        response = await client.post("/api/v1/forgot-password", json=payload)
        
        # Должно вернуть такое же сообщение (безопасность)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_verify_reset_code_invalid(self, client):
        """Проверка неверного кода сброса"""
        payload = {
            "email": "test@example.com",
            "code": "000000"
        }
        
        response = await client.post("/api/v1/verify-reset-code", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False
    
    @pytest.mark.asyncio
    async def test_verify_reset_code_invalid_format(self, client):
        """Проверка кода неверного формата"""
        payload = {
            "email": "test@example.com",
            "code": "12345"  # 5 цифр вместо 6
        }
        
        response = await client.post("/api/v1/verify-reset-code", json=payload)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_reset_password_with_token(self, client, db_session, test_user):
        """Сброс пароля с токеном"""
        # Создаем токен сброса
        from coffee_backend.app.services.password_reset_service import PasswordResetService
        
        raw_token, _ = await PasswordResetService.create_reset_request(
            db=db_session,
            email=test_user[0].email
        )
        
        payload = {
            "token": raw_token,
            "new_password": "NewSecurePass123!"
        }
        
        response = await client.post("/api/v1/reset-password", json=payload)
        
        assert response.status_code == 200
        
        # Проверяем, что пароль изменился
        result = await db_session.execute(
            select(User).where(User.id == test_user[0].id)
        )
        user = result.scalar_one()
        
        assert await verify_password("NewSecurePass123!", user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self, client, db_session, test_user):
        """Сброс пароля с истекшим токеном"""
        from coffee_backend.app.models.models import PasswordResetToken
        
        # Создаем истекший токен
        expired_token = PasswordResetToken(
            user_id=test_user[0].id,
            token_hash="expired_hash",
            code="123456",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used=False
        )
        db_session.add(expired_token)
        await db_session.commit()
        
        payload = {
            "token": "expired_token_value",
            "new_password": "NewSecurePass123!"
        }
        
        response = await client.post("/api/v1/reset-password", json=payload)
        
        assert response.status_code == 400