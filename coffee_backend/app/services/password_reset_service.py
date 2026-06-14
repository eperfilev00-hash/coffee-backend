import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from coffee_backend.app.models.models import User
from coffee_backend.app.models.models import PasswordResetToken
from coffee_backend.app.config import settings


class PasswordResetService:
    """Сервис для управления токенами сброса пароля."""
    
    TOKEN_EXPIRY_MINUTES = 60  # Время жизни токена
    CODE_LENGTH = 6
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Хеширует токен перед сохранением в БД (безопасность)."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def _generate_secure_code() -> str:
        """Генерирует 6-значный код для сброса."""
        import secrets
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @classmethod
    async def create_reset_request(
        cls,
        db: AsyncSession,
        email: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Создаёт запрос на сброс пароля.
        
        Args:
            db: Сессия БД
            email: Email пользователя
            
        Returns:
            Tuple: (raw_token, code) или (None, None) если пользователь не найден
        """
        # Ищем пользователя
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            # ⚠️ НЕ сообщаем, что пользователь не найден (защита от перебора email)
            return None, None
        
        if not user.is_active:
            return None, None
        
        # Очищаем старые токены для этого пользователя
        await cls._invalidate_user_tokens(db, user.id)
        
        # Генерируем новый токен и код
        raw_token, code = PasswordResetToken.generate_token()
        token_hash = cls._hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=cls.TOKEN_EXPIRY_MINUTES)
        
        # Создаём запись в БД
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            code=code,
            expires_at=expires_at,
            used=False
        )
        
        db.add(reset_token)
        await db.flush()
        await db.commit()        
        
        return raw_token, code
    
    @classmethod
    async def _invalidate_user_tokens(cls, db: AsyncSession, user_id: int) -> None:
        """Отзывает все активные токены пользователя."""
        result = await db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.used == False
                )
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.used = True
        await db.flush()
        await db.commit()
    
    @classmethod
    async def verify_code(
        cls,
        db: AsyncSession,
        email: str,
        code: str
    ) -> Optional[int]:
        """
        Проверяет код сброса пароля.
        
        Args:
            db: Сессия БД
            email: Email пользователя
            code: 6-значный код
            
        Returns:
            user_id если код валиден, None иначе
        """
        # Ищем пользователя
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Ищем активный токен с этим кодом
        result = await db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.code == code,
                    PasswordResetToken.used == False,
                    PasswordResetToken.expires_at > datetime.now(timezone.utc)
                )
            )
        )
        token = result.scalar_one_or_none()
        
        if not token:
            return None
        
        return user.id
    
    @classmethod
    async def verify_token(
        cls,
        db: AsyncSession,
        raw_token: str
    ) -> Optional[PasswordResetToken]:
        """
        Проверяет токен сброса (для URL-ссылки).
        
        Args:
            db: Сессия БД
            raw_token: Сырой токен из URL
            
        Returns:
            PasswordResetToken если валиден, None иначе
        """
        token_hash = cls._hash_token(raw_token)
        
        result = await db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.used == False,
                    PasswordResetToken.expires_at > datetime.now(timezone.utc)
                )
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def mark_token_as_used(
        cls,
        db: AsyncSession,
        token: PasswordResetToken
    ) -> None:
        """Отмечает токен как использованный."""
        token.used = True
        await db.commit()
    
    @classmethod
    async def cleanup_expired_tokens(cls, db: AsyncSession) -> int:
        """
        Удаляет просроченные токены.
        
        Returns:
            int: Количество удалённых токенов
        """
        from sqlalchemy import delete
        
        # Сначала считаем сколько токенов будет удалено
        count_result = await db.execute(
            select(func.count()).where(
                PasswordResetToken.expires_at < datetime.now(timezone.utc)
            )
        )
        count_before = count_result.scalar() or 0
        
        result = await db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await db.commit()
        return count_before