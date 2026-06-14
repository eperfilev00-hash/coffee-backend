import pytest

class TestTOTPEndpoints:
    """Тесты TOTP настройки и управления"""
    
    @pytest.mark.asyncio
    async def test_totp_setup(self, authenticated_client, test_user):
        """Настройка TOTP"""
        payload = {"password": "testpass123"}
        
        response = await authenticated_client.post("/api/v1/totp/setup", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_uri" in data
        assert "manual_entry_code" in data
    
    @pytest.mark.asyncio
    async def test_totp_setup_wrong_password(self, authenticated_client, test_user):
        """Настройка TOTP с неверным паролем"""
        payload = {"password": "wrongpassword"}
        
        response = await authenticated_client.post("/api/v1/totp/setup", json=payload)
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_totp_verify_success(self, authenticated_client, test_user):
        """Успешная верификация TOTP"""
        import pyotp
        
        # Настройка
        setup_response = await authenticated_client.post(
            "/api/v1/totp/setup",
            json={"password": "testpass123"}
        )
        secret = setup_response.json()["secret"]
        
        # Получение кода
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # Верификация
        response = await authenticated_client.post(
            "/api/v1/totp/verify",
            json={"token": code}
        )
        
        assert response.status_code == 200
        assert "successfully enabled" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_totp_verify_wrong_code(self, authenticated_client, test_user):
        """Верификация с неверным TOTP кодом"""
        response = await authenticated_client.post(
            "/api/v1/totp/verify",
            json={"token": "000000"}
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_totp_status(self, authenticated_client, test_user):
        """Проверка статуса TOTP"""
        response = await authenticated_client.get("/api/v1/totp/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "totp_enabled" in data
        assert "totp_setup" in data
    
    @pytest.mark.asyncio
    async def test_totp_disable(self, authenticated_client, test_user):
        """Отключение TOTP"""
        import pyotp
        
        # Включаем TOTP
        setup_response = await authenticated_client.post(
            "/api/v1/totp/setup",
            json={"password": "testpass123"}
        )
        secret = setup_response.json()["secret"]
        code = pyotp.TOTP(secret).now()
        
        await authenticated_client.post(
            "/api/v1/totp/verify",
            json={"token": code}
        )
        
        # Отключаем
        response = await authenticated_client.post(
            "/api/v1/totp/disable",
            json={"token": pyotp.TOTP(secret).now()}
        )
        
        assert response.status_code == 200
        assert "successfully disabled" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_totp_disable_when_not_enabled(self, authenticated_client, test_user):
        """Отключение TOTP когда он не включен"""
        response = await authenticated_client.post(
            "/api/v1/totp/disable",
            json={"token": "123456"}
        )
        
        assert response.status_code == 400