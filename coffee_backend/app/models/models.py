import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field
from sqlalchemy import TIMESTAMP, Time, Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, SmallInteger, String, func
from sqlalchemy.orm import mapped_column,Mapped, relationship
from coffee_backend.app.models.base import Base



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
    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    customer_name:Mapped[str] = mapped_column(String(200),nullable=False)
    points_balance:Mapped[int] = mapped_column(Integer,default=0, nullable=False)
    tier:Mapped[str] = mapped_column(String(20),default='bronze', nullable=False)

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

