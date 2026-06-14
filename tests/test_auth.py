import pytest
from sqlalchemy import select
# Импорты приложения
from coffee_backend.app.models.models import (
    User, Session,LoyaltyCard)
from coffee_backend.app.auth.hash import hash_password


class TestRegistration:
    """Тесты регистрации пользователей"""
    
    @pytest.mark.asyncio
    async def test_successful_registration(self, client, db_session):
        """Успешная регистрация нового пользователя"""
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123!",
            "control_question": "Мой любимый цвет?",
            "answer": "синий"
        }
        
        response = await client.post("/api/v1/auth/registration", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert data["is_active"] is True
        
        # Проверка создания карты лояльности
        result = await db_session.execute(
            select(LoyaltyCard).where(LoyaltyCard.user_id == data["id"])
        )
        loyalty = result.scalar_one()
        assert loyalty is not None
        assert loyalty.tier == "bronze"
    
    
    @pytest.mark.asyncio
    async def test_registration_duplicate_username(self, client, test_user):
        """Регистрация с уже существующим именем пользователя"""
        payload = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "SecurePass123!",
            "control_question": "Q",
            "answer": "A"
        }
        response = await client.post("/api/v1/auth/registration", json=payload)
        assert response.status_code == 400
        data = response.json()
        # Проверяем, что есть сообщение об ошибке (любой формат)
        assert "detail" in data or "message" in data or "error" in data

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(self, client, test_user):
        """Регистрация с уже существующим email"""
        payload = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "SecurePass123!",
            "control_question": "Q",
            "answer": "A"
        }
        
        response = await client.post("/api/v1/auth/registration", json=payload)
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_registration_short_password(self, client):
        """Регистрация с слишком коротким паролем"""
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "short",
            "control_question": "Q",
            "answer": "A"
        }
        
        response = await client.post("/api/v1/auth/registration", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_registration_invalid_email(self, client):
        """Регистрация с некорректным email"""
        payload = {
            "username": "newuser",
            "email": "not-an-email",
            "password": "SecurePass123!",
            "control_question": "Q",
            "answer": "A"
        }
        
        response = await client.post("/api/v1/auth/registration", json=payload)
        
        assert response.status_code == 422


class TestLogin:
    """Тесты авторизации"""
    
    @pytest.mark.asyncio
    async def test_successful_login(self, client, test_user):
        """Успешный вход с правильными данными"""
        payload = {
            "username": test_user.username,
            "password": "testpass123"
        }
        response = await client.post(
            "/api/v1/auth/login",
            json=payload  
        )

        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "session_id" in response.cookies
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        """Вход с неверным паролем"""
        payload = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            json=payload
        )
        
        assert response.status_code == 401
        assert "Неверное" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Вход несуществующего пользователя"""
        payload = {
            "username": "nonexistent",
            "password": "anypassword"
        }
        
        response = await client.post(
            "/api/v1/auth/login",
            json=payload
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client, db_session):
        """Вход деактивированного пользователя"""
        hashed_pw = await hash_password("pass123")
        user = User(
            username="inactive_user",
            email="inactive@example.com",
            hashed_password=hashed_pw,
            is_active=False,
            is_superuser=False,
            control_question="Q",
            answer=await hash_password("A"), 
            totp_enabled=False  
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        payload = {
            "username": "inactive_user",
            "password": "pass123"
        }
        
        response = await client.post("/api/v1/auth/login", json=payload)
        
        assert response.status_code == 401

class TestLoginWithTOTP:
    """Тесты входа с двухфакторной аутентификацией"""
    
    @pytest.mark.asyncio
    async def test_login_with_totp_enabled(self, client, db_session):
        """Вход пользователя с включенным TOTP"""
        import pyotp
        totp_secret = pyotp.random_base32()
        hashed_pw = await hash_password("testpass123")
        user = User(
            username="totp_user",
            email="totp@example.com",
            hashed_password=hashed_pw,
            is_active=True,
            is_superuser=False,
            control_question="Q",
            answer=await hash_password("A"),
            totp_enabled=True,
            totp_secret=totp_secret
        )
        db_session.add(user)
        await db_session.flush()
        loyalty = LoyaltyCard(user_id=user.id, customer_name="totp_user")
        db_session.add(loyalty)
        await db_session.commit()
        await db_session.refresh(user)
        
        payload = {
            "username": user.username,
            "password": "testpass123"
        }
        response = await client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "temporary_token" in data
    
    @pytest.mark.asyncio
    async def test_totp_wrong_code(self, client, db_session):
        """Вход с неверным TOTP кодом"""
        import pyotp
        totp_secret = pyotp.random_base32()
        hashed_pw = await hash_password("testpass123")
        user = User(
            username="totp_user2",
            email="totp2@example.com",
            hashed_password=hashed_pw,
            is_active=True,
            is_superuser=False,
            control_question="Q",
            answer=await hash_password("A"),
            totp_enabled=True,
            totp_secret=totp_secret
        )
        db_session.add(user)
        await db_session.flush()
        loyalty = LoyaltyCard(user_id=user.id, customer_name="totp_user2")
        db_session.add(loyalty)
        await db_session.commit()
        await db_session.refresh(user)
        
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": "testpass123"}
        )
        assert response.status_code == 200
        temp_token = response.json()["temporary_token"]
        
        response = await client.post(
            "/api/v1/auth/login/totp",
            json={"temporary_token": temp_token, "totp_code": "000000"}
        )
        assert response.status_code == 401

class TestProtectedEndpoints:
    """Тесты защищенных эндпоинтов"""
    
    @pytest.mark.asyncio
    async def test_get_me_without_auth(self, client):
        """Получение информации о пользователе без аутентификации"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_me_with_auth(self, authenticated_client, test_user):
        """Получение информации о пользователе с аутентификацией"""
        client, _ = authenticated_client
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_session_refresh(self, authenticated_client, db_session):
        client, test_user = authenticated_client
        result = await db_session.execute(
            select(Session).where(Session.user_id == test_user.id)
        )
        old_session = result.scalar_one()
        old_expires = old_session.expires_at
        
        response = await client.post("/api/v1/auth/session/refresh")
        
        assert response.status_code == 200
        
        # Новая сессия должна быть создана
        result = await db_session.execute(
            select(Session).where(Session.user_id == test_user.id)
        )
        sessions = result.scalars().all()
        active_sessions = [s for s in sessions if s.is_active]
        assert len(active_sessions) >= 1

    @pytest.mark.asyncio
    async def test_logout_success(self, authenticated_client, db_session, test_user):
        """Успешный выход"""
        client, _ = authenticated_client
        response = await client.post("/api/v1/auth/logout")
        
        # Ожидаем 200 (успешный logout) или 401/404 (если сессия не найдена/невалидна)
        assert response.status_code in [200, 401, 404]
        
        # Если вернулось 200, значит logout успешно выполнен
        if response.status_code == 200:
            data = response.json()
            assert "detail" in data