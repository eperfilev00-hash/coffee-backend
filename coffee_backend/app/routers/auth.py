from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, HTTPException, Request, status, Response, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from coffee_backend.app.auth.dependencies import get_current_user
from coffee_backend.app.auth.deps.rate_limit import rate_limit_login, rate_limit_refresh, rate_limit_registration, rate_limit_totp
from coffee_backend.app.auth.hash import hash_password, verify_password
from coffee_backend.app.auth.totp import verify_totp
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import LoyaltyCard, Session, User
from coffee_backend.app.schemas import TOTPLoginRequest, UserCreate, UserLogin, UserResponse
router = APIRouter(tags=["Аутентификация"])


@router.post('/registration', status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def registration(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_registration)
) -> UserResponse:
    # Проверка на существование пользователя
    result = await db.execute(
        select(User).where((User.username == user_data.username) | (User.email == user_data.email))
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь с таким именем или email уже существует'
        )

    # Хеширование пароля и на контрольный вопрос
    hashed_password = await hash_password(user_data.password)
    hashed_answer = await hash_password(user_data.answer)
    
    # Создание пользователя
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        control_question=user_data.control_question,
        answer=hashed_answer ,
        totp_enabled=False
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    
    user_data_dict = {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at
    }
    
    # Создание карты лояльности
    loyalty_card = LoyaltyCard(
        user_id=user_data_dict["id"],
        customer_name=user_data_dict["username"],
        points_balance=0,
        tier='bronze'
    )
    db.add(loyalty_card)
    await db.commit() 

    return UserResponse(**user_data_dict)

@router.post('/login')
async def login(
    user_data: UserLogin,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_login)
):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Поиск пользователя
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Неверное имя пользователя или пароль'
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Пользователь деактивирован'
            )
        # Проверка пароля
        if not await verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Неверное имя пользователя или пароль'
            )
        
        # Сохраняем данные пользователя ДО commit()
        user_id = user.id
        user_username = user.username
        user_email = user.email
        user_is_active = user.is_active
        user_created_at = user.created_at
        
        # Проверка TOTP если включена
        if user.totp_enabled:
            if not user.totp_secret:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail='TOTP configuration error'
                )
            
            # Создаём временную pending-сессию (5 минут)
            temp_session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

            temp_session = Session(
                session_id=temp_session_id,
                user_id=user_id,
                expires_at=expires_at,
                is_pending=True,
                ip_address=request.client.host if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None
            )
            db.add(temp_session)
            await db.commit()

            return {
                "temporary_token": temp_session_id,
                "message": "2FA code required",
                "username": user_username
            }
        
        # Если 2FA не включена - создаём обычную сессию
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        db.add(session)
        await db.commit()

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=604800,
            path="/"
        )
        
        return UserResponse(
            id=user_id,
            username=user_username,
            email=user_email,
            is_active=user_is_active,
            created_at=user_created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка при авторизации')

@router.post('/login/totp')
async def login_totp(
    totp_data: TOTPLoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_totp)
):
    """
    Второй шаг логина с TOTP кодом.
    Используется temporary_token из первого шага.
    """
    try:
        # Ищем pending-сессия по временному токену
        result = await db.execute(
            select(Session).where(
                Session.session_id == totp_data.temporary_token,
                Session.is_pending == True,
                Session.is_active == True
            )
        )
        temp_session = result.scalar_one_or_none()
        
        if not temp_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Неверный или истёкший временный токен'
            )
        
        # Проверяем срок действия (5 минут)
        if datetime.now(timezone.utc) > temp_session.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Временный токен истёк'
            )
        
        # Находим пользователя
        result = await db.execute(
            select(User).where(User.id == temp_session.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Пользователь не найден'
            )
        
        # Сохраняем данные пользователя ДО commit()
        user_id = user.id
        user_username = user.username
        user_email = user.email
        user_is_active = user.is_active
        user_created_at = user.created_at
        
        if not user.totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='TOTP не включен для этого пользователя'
            )
        
        if not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='TOTP configuration error'
            )
        
        # Проверяем TOTP код
        if not verify_totp(user.totp_secret, totp_data.totp_code, window=1):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Неверный TOTP код'
            )
        
        # --- УСПЕШНАЯ ПРОВЕРКА 2FA ---
        
        # Деактивируем временную сессию
        temp_session.is_active = False
        temp_session.is_pending = False
        await db.commit()
        
        # Создаём полноценную сессию
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(session)
        await db.commit()

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=604800,
            path="/"
        )
        
        return UserResponse(
            id=user_id,
            username=user_username,
            email=user_email,
            is_active=user_is_active,
            created_at=user_created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Login TOTP error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка при проверке 2FA кода'
        )

@router.post('/logout')
async def logout(
    response: Response,
    request: Request,  # <-- добавить request
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Завершение сессии и удаление куки."""
    # Получаем session_id из куки
    session_id = request.cookies.get("session_id")
    if session_id:
        result = await db.execute(
            select(Session)
            .where(Session.session_id == session_id)
            .where(Session.is_active == True)
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await db.commit()
    
    response.delete_cookie(
        key="session_id",
        path="/"
    )
    
    return {"detail": "Successfully logged out"}

@router.post('/session/refresh')
async def refresh_session(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_refresh)
):
    """Продление сессии."""
    # Деактивируем старую сессию
    session_id = request.cookies.get("session_id")
    if session_id:
        result = await db.execute(
            select(Session).where(Session.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
    
    # Создаём новую сессию
    new_session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    new_session = Session(
        session_id=new_session_id,
        user_id=current_user.id,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(new_session)
    await db.commit()
    
    response.set_cookie(
        key="session_id",
        value=new_session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
        path="/"
    )
    
    return {"detail": "Session refreshed"}

@router.get('/me', response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе.
    
    Использует зависимость get_current_user для автоматической валидации токена.
    """
    try:
        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ошибка при получении информации о пользователе'
        )