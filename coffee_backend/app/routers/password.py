from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from coffee_backend.app.auth.deps.rate_limit import rate_limit_forgot_password, rate_limit_reset_password, rate_limit_verify_reset_code
from coffee_backend.app.auth.hash import hash_password
from coffee_backend.app.database import get_db
from coffee_backend.app.config import settings
from coffee_backend.app.models.models import PasswordResetToken, User
from coffee_backend.app.schemas import (
    ForgotPasswordRequest,
    ResetPasswordByCodeRequest,
    VerifyResetCodeRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    VerifyCodeResponse
)
from coffee_backend.app.services.password_reset_service import PasswordResetService
from coffee_backend.app.services.email_service import send_password_reset_email

router = APIRouter(tags=['Сброс пароля'])


@router.post('/forgot-password', status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_forgot_password)
):
    """
    Инициация сброса пароля.
    
    Отправляет email с кодом подтверждения.
    ⚠️ Всегда возвращает одинаковое сообщение (безопасность).
    """
    # Создаём запрос на сброс
    raw_token, reset_code = await PasswordResetService.create_reset_request(
        db=db,
        email=request.email
    )
    
    # ⚠️ Никогда не сообщаем, существует ли пользователь
    # Это защищает от перебора email (user enumeration)
    
    if raw_token and reset_code:
        # Отправляем email асинхронно
        reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"
        background_tasks.add_task(
            send_password_reset_email,
            request.email,
            reset_code,
            reset_link
        )
    
    return {
        "detail": "Если ваш email зарегистрирован, на него отправлен код для сброса пароля"
    }


@router.post('/verify-reset-code', status_code=status.HTTP_200_OK)
async def verify_reset_code(
    request: VerifyResetCodeRequest,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_verify_reset_code)
) -> VerifyCodeResponse:
    """
    Проверка кода сброса пароля.
    
    Проверяет 6-значный код из email.
    """
    user_id = await PasswordResetService.verify_code(
        db=db,
        email=request.email,
        code=request.code
    )
    
    if not user_id:
        # ⚠️ Не раскрываем причину ошибки
        return VerifyCodeResponse(
            verified=False,
            message="Неверный код или код истёк"
        )
    
    return VerifyCodeResponse(
        verified=True,
        message="Код подтверждён. Теперь вы можете установить новый пароль."
    )


@router.post('/reset-password', status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_reset_password)
) -> ResetPasswordResponse:
    """
    Сброс пароля после успешной верификации.
    """
    # Проверяем токен
    reset_token = await PasswordResetService.verify_token(
        db=db,
        raw_token=request.token
    )
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истёкший токен сброса"
        )
    
    # Проверяем, что пользователь активен
    result = await db.execute(
        select(User).where(User.id == reset_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден или отключён"
        )
    
    # Хешируем новый пароль
    hashed_password = await hash_password(request.new_password)
    user.hashed_password = hashed_password
    
    # Отмечаем токен как использованный
    await PasswordResetService.mark_token_as_used(db, reset_token)
    
    # ⚠️ Дополнительно: отзываем все сессии пользователя
    # (можно реализовать через чёрный список JWT токенов)
    
    await db.commit()
    
    return ResetPasswordResponse(
        success=True,
        message="Пароль успешно изменён. Теперь вы можете войти с новым паролем."
    )

@router.post('/reset-password-by-code', status_code=status.HTTP_200_OK)
async def reset_password_by_code(
    request: ResetPasswordByCodeRequest,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_reset_password)
) -> ResetPasswordResponse:
    """
    Сброс пароля по 6-значному коду из email.
    
    Альтернативный flow: email → code → new_password (без токена из URL)
    """
    # Ищем пользователя по email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден или отключён"
        )
    
    # Ищем активный токен с этим кодом
    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.code == request.code,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.now(timezone.utc)
            )
        )
    )
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код или код истёк"
        )
    
    # Хешируем новый пароль
    hashed_password = await hash_password(request.new_password)
    user.hashed_password = hashed_password
    
    # Отмечаем токен как использованный
    token.used = True
    
    # Дополнительно: отмечаем все другие токены пользователя как использованные
    await db.execute(
        update(PasswordResetToken)
        .where(
            and_(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.id != token.id
            )
        )
        .values(used=True)
    )
    
    await db.commit()
    
    return ResetPasswordResponse(
        success=True,
        message="Пароль успешно изменён. Теперь вы можете войти с новым паролем."
    )


@router.post('/send-otp-reset', status_code=status.HTTP_200_OK)
async def send_otp_reset(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Альтернативный метод: отправка OTP кода только для проверки.
    
    Не создаёт токен, только код для верификации.
    Полезно для flow: email → code → new_password (без URL токена)
    """
    # Аналогично forgot_password, но без токена
    _, reset_code = await PasswordResetService.create_reset_request(
        db=db,
        email=request.email
    )
    
    if reset_code:
        background_tasks.add_task(
            send_password_reset_email,
            request.email,
            reset_code,
            reset_link=None  # Только код, без ссылки
        )
    
    return {
        "detail": "Если ваш email зарегистрирован, на него отправлен код для сброса пароля"
    }