from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from coffee_backend.app.auth.dependencies import get_current_user
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import OrderItem, User, Order
from coffee_backend.app.schemas import OrderCreateRequest, OrderItemResponse, OrderResponse
from coffee_backend.app.services.order_services import create_order

router = APIRouter(tags=['Заказы'])


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def place_order(
    order_data: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание заказа (требуется аутентификация)."""
    async with db.begin():
        order_response = await create_order(db, order_data, current_user) 
    
    return order_response


@router.get('/orders/{order_id}', status_code=status.HTTP_200_OK, response_model=OrderResponse)
async def status_order(
    order_id: int,
    current_user: User = Depends(get_current_user),  
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о заказе (требуется аутентификация)."""
    result = await db.execute(
        select(Order).options(
            joinedload(Order.items).joinedload(OrderItem.menu_item)
        ).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    items_resp = [
        OrderItemResponse(
            menu_item_id=oi.menu_item_id,
            name=oi.menu_item.name if oi.menu_item else "Unknown",
            quantity=oi.quantity,
            item_price=float(oi.item_price_at_time),
            total_line=float(oi.quantity * oi.item_price_at_time)
        )
        for oi in order.items
    ]
    
    points_earned = order.points_earned
    
    return OrderResponse(
        id=order.id,
        items=items_resp,
        total_price=float(order.total_price),
        discount_applied=float(order.discount_applied),
        final_price=float(order.final_price),
        points_earned=points_earned,
        status=order.status,
        created_at=order.created_at
    )


@router.get('/orders', response_model=list[OrderResponse])
async def list_user_orders(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получение истории заказов текущего пользователя."""
    # Найти loyalty card пользователя
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user or not user.loyalty_card:
        raise HTTPException(status_code=404, detail="No loyalty card found")
    
    result = await db.execute(
        select(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
        .where(Order.card_id == user.loyalty_card.id)
        .offset(skip)
        .limit(limit)
    )
    orders = result.scalars().all()
    
    return [
        OrderResponse(
            id=order.id,
            items=[
                OrderItemResponse(
                    menu_item_id=oi.menu_item_id,
                    name=oi.menu_item.name if oi.menu_item else "Unknown",
                    quantity=oi.quantity,
                    item_price=float(oi.item_price_at_time),
                    total_line=float(oi.quantity * oi.item_price_at_time)
                )
                for oi in order.items
            ],
            total_price=float(order.total_price),
            discount_applied=float(order.discount_applied),
            final_price=float(order.final_price),
            points_earned=order.points_earned,
            status=order.status,
            created_at=order.created_at
        )
        for order in orders
    ]