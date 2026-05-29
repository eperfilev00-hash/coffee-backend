from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from coffee_backend.app.models.models import MenuItem, OrderItem
from coffee_backend.app.schemas import OrderCreateRequest, OrderItemResponse, OrderResponse
from coffee_backend.app.database import get_db
from coffee_backend.app.services.order_services import create_order
from coffee_backend.app.models import Order

router = APIRouter()

@router.post("/orders", response_model=OrderResponse, status_code=201)
async def place_order(order_data: OrderCreateRequest, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        order_response = await create_order(db, order_data)
    
    return order_response
    
@router.get('/orders/{order_id}', status_code=status.HTTP_200_OK, response_model=OrderResponse)
async def status_order(order_id: int, db: AsyncSession = Depends(get_db)):
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
    
    # Формируем ответ
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