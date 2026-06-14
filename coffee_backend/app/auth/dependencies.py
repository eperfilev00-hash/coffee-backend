from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from sqlalchemy.orm import selectinload

from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import User, Session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя из сессионной куки.
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Найти активную сессию
    result = await db.execute(
        select(Session)
        .where(Session.session_id == session_id)
        .where(Session.is_active == True)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Проверка истечения сессии
    if session.expires_at < datetime.now(timezone.utc):
        session.is_active = False
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Получить пользователя с подгрузкой loyalty_card
    result = await db.execute(
        select(User)
        .where(User.id == session.user_id)
        .options(selectinload(User.loyalty_card))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Получение текущего суперпользователя (администратора).
    Проверяет, что пользователь аутентифицирован и имеет права суперпользователя.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )
    return current_user