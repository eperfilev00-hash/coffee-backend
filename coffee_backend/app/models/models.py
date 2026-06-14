import datetime
from decimal import Decimal
import secrets
from typing import Optional

from pydantic import Field
from sqlalchemy import TIMESTAMP, Time, Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, SmallInteger, String, func
from sqlalchemy.orm import mapped_column,Mapped, relationship
from coffee_backend.app.models.base import Base


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    control_question: Mapped[str] = mapped_column(String(255), nullable=False)
    answer: Mapped[str] = mapped_column(String(255), nullable=False)
    
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)  
    totp_secret_pending: Mapped[str] = mapped_column(String(255), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    loyalty_card = relationship("LoyaltyCard", back_populates="user", uselist=False)
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[Optional[datetime.datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    
    __table_args__ = (
        CheckConstraint('username != \'\'', name='check_mapped_username_not_empty'),
        CheckConstraint('email LIKE \'%@%\'', name='check_email_valid'),
    )

class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True,nullable=False)
    session_id: Mapped[str] = mapped_column(String(255),unique=True,index=True,nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'),nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    ) 
    expires_at:Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True),nullable=False)
    is_active:Mapped[bool] = mapped_column(default=True,nullable=False)
    is_pending:Mapped[bool] = mapped_column(default=False,nullable=False)  # Для ожидания 2FA
    ip_address: Mapped[Optional[str]] = mapped_column(String(45),nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255),nullable=True)

class PasswordResetToken(Base):
    """Модель для токенов сброса пароля."""
    __tablename__ = "password_reset_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # Хеш токена (не сам токен)
    code: Mapped[str] = mapped_column(String(6), nullable=False)  # 6-значный код для SMS/email
    expires_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    
    user = relationship("User", backref="password_reset_tokens")
    
    __table_args__ = (
        # Индекс для быстрого поиска не использованных токенов
        Index('idx_token_hash_used_expires', 'token_hash', 'used', 'expires_at'),
    )
    
    @classmethod
    def generate_token(cls) -> tuple[str, str]:
        """
        Генерирует безопасный токен и код.
        
        Returns:
            tuple: (raw_token, code) - токен для URL и 6-значный код
        """
        # Генерируем криптографически безопасный токен
        raw_token = secrets.token_urlsafe(32)  # 256 бит
        
        # Генерируем 6-значный код для email/SMS
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        return raw_token, code
    

class Ingredient(Base):
    __tablename__ = "ingredients"
    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    name:Mapped[str] = mapped_column(String(100),nullable=False,unique=True)
    stock_quantity:Mapped[Decimal] = mapped_column(Numeric(10,2),nullable=False)
    unit:Mapped[str] = mapped_column(String(20),nullable=False)
    low_stock_threshold:Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)

    __table_args__ = (
        CheckConstraint('stock_quantity >= 0', name='check_stock_positive'),
    )

class MenuItem(Base):
    __tablename__ = 'menu_items'
    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    name:Mapped[str] = mapped_column(String(100),nullable=False)
    base_price:Mapped[Decimal] = mapped_column(Numeric(8,2),nullable=False)
    is_available:Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        CheckConstraint('base_price > 0', name='check_base_price_positive'),
    )

class Recipe(Base):
    __tablename__ = 'recipes'
    menu_item_id:Mapped[int] = mapped_column(ForeignKey("menu_items.id",ondelete='CASCADE'), primary_key=True)
    ingredient_id:Mapped[int] = mapped_column(ForeignKey("ingredients.id"), primary_key=True)
    quantity_used:Mapped[Decimal] = mapped_column(Numeric(10,2),nullable=False)
    
class PricingRule(Base):
    __tablename__ = 'pricing_rules'
    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    multiplier:Mapped[Decimal] = mapped_column(Numeric(8,2),nullable=False)
    
    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_start_end'),
        CheckConstraint('day_of_week BETWEEN 0 AND 6',name='check_day_of_week_range'),
        CheckConstraint('multiplier >= 0.5',name='check_multiplier_positive'),
        Index('idx_pricing_time', 'day_of_week', 'start_time', 'end_time'),
    )

class LoyaltyCard(Base):
    __tablename__ = 'loyalty_cards'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), unique=True, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default='bronze', nullable=False)
    
    user = relationship("User", back_populates="loyalty_card")
    
    __table_args__ = (
        CheckConstraint('points_balance >= 0', name='check_points_balance_positive'),
    )


class LoyaltyTier(Base):
    __tablename__ = 'loyalty_tiers'    
    tier_name:Mapped[str] = mapped_column(String(20),primary_key=True)
    discount_percent:Mapped[Decimal] = mapped_column(Numeric(4,2),nullable=False)
    points_multiplier:Mapped[Decimal] = mapped_column(Numeric(3,2),default=1.0,nullable=False)
    min_points_for_tier:Mapped[int] = mapped_column(Integer,default=0,nullable=False)

    __table_args__ = (
        CheckConstraint('tier_name != \'\'', name='check_tier_name_not_empty'),
        CheckConstraint('discount_percent >= 0 AND discount_percent <= 100', name='check_discount_percent_positive')
    )

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('loyalty_cards.id'))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_applied: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    final_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='new')
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('new', 'confirmed', 'preparing', 'completed', 'cancelled')",
            name='check_status_valid'
        ),
    )
    items = relationship("OrderItem", back_populates="order", lazy="raise")
class OrderItem(Base):
    __tablename__ = 'order_items'
    order_id:Mapped[int] = mapped_column(Integer,ForeignKey('orders.id',ondelete='CASCADE'),primary_key=True)
    menu_item_id:Mapped[int] = mapped_column(Integer,ForeignKey('menu_items.id'),primary_key=True)
    quantity:Mapped[int] = mapped_column(Integer,nullable=False)
    item_price_at_time:Mapped[Decimal] = mapped_column(Numeric(8,2),nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0",name='check_quantity_valid'),
    )
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", lazy="raise")  # для доступа к name

