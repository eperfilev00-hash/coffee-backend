from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from authx import AuthX

from coffee_backend.app.auth.dependencies import get_current_user
from coffee_backend.app.auth.hash import verify_password
from coffee_backend.app.auth.totp import generate_top_secret, generate_top_url, get_current_totp, verify_totp
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import User
from coffee_backend.app.schemas import TOTPSetupRequest, TOTPSetupResponse, TOTPVerifyRequest, EnableTOTPRequest

router = APIRouter(tags=['Безопасность'])


@router.post('/totp/setup', response_model=TOTPSetupResponse)
async def setup_totp(
    request: TOTPSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Настройка TOTP (2FA).
    
    1. Проверяет пароль пользователя
    2. Генерирует новый TOTP секрет
    3. Возвращает QR-код и секрет для ручной установки
    
    ⚠️ TOTP не активируется сразу - требуется верификация кодом
    """
    # Проверка пароля
    if not await verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password"
        )
    
    # Генерация нового секрета
    totp_secret = generate_top_secret()
    
    # Генерация URI для QR-кода
    qr_uri = generate_top_url(
        secret=totp_secret,
        email=current_user.email,
        issuer='CoffeeApp'
    )
    
    # Получение кода для ручной установки
    manual_entry_code = get_current_totp(totp_secret)
    
    # ⚠️ ИСПРАВЛЕНИЕ: Сохраняем секрет ВРЕМЕННО в отдельное поле
    # не перезаписывая текущий, если он уже есть
    current_user.totp_secret_pending = totp_secret  # Новое поле в модели
    
    await db.commit()
    
    return TOTPSetupResponse(
        secret=totp_secret,
        qr_uri=qr_uri,
        manual_entry_code=manual_entry_code
    )


@router.post('/totp/verify')
async def verify_totp_code(
    request: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Верификация TOTP кода для подтверждения настройки.
    
    Если код верный - активирует TOTP.
    """
    totp_secret = current_user.totp_secret_pending or current_user.totp_secret
    
    if not totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP not set up. Call /totp/setup first"
        )
    
    if not verify_totp(totp_secret, request.token, window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )
    
    if current_user.totp_secret_pending:
        current_user.totp_secret = current_user.totp_secret_pending
        current_user.totp_secret_pending = None # type: ignore
    
    current_user.totp_enabled = True
    await db.commit()
    
    return {"detail": "TOTP successfully enabled"}


@router.post('/totp/disable')
async def disable_totp(
    request: EnableTOTPRequest,  # Используем тот же schema для кода подтверждения
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Отключение TOTP.
    
    Требует текущий TOTP код для подтверждения.
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP is not enabled"
        )
    if current_user.totp_secret:
        if not verify_totp(current_user.totp_secret, request.token, window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
    
    # Отключаем TOTP
    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()
    
    return {"detail": "TOTP successfully disabled"}


@router.get('/totp/status')
async def get_totp_status(
    current_user: User = Depends(get_current_user)
):
    """Получение статуса TOTP для текущего пользователя."""
    return {
        "totp_enabled": current_user.totp_enabled,
        "totp_setup": current_user.totp_secret is not None
    }