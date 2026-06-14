from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from coffee_backend.app.models.models import LoyaltyCard, MenuItem, Order, OrderItem, User
from coffee_backend.app.schemas import OrderCreateRequest, OrderResponse, OrderItemResponse
from coffee_backend.app.services.inventory import check_and_reserve_stock
from coffee_backend.app.services.loyalty_services import calculate_final_price, get_tier_discount, recalc_tier
from coffee_backend.app.services.pricing import get_current_multiplier


async def create_order(db_session: AsyncSession, order_data: OrderCreateRequest,current_user:User) -> OrderResponse:
        # 1. Проверить дубликаты menu_item_id
        seen_items = set()
        for item in order_data.items:
            if item.menu_item_id in seen_items:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Дубликат menu_item_id: {item.menu_item_id}"
                )
            seen_items.add(item.menu_item_id)

        # 2. Получить текущий множитель
        multiplier = await get_current_multiplier(db_session)

        # 3. Рассчитать базовую цену каждой позиции (используем Decimal)
        menu_item_ids = [item.menu_item_id for item in order_data.items]
        result = await db_session.execute(
            select(MenuItem).where(MenuItem.id.in_(menu_item_ids))
        )
        all_menu_items = {item.id: item for item in result.scalars()}

        # Проверить наличие и доступность
        for menu_item_id in menu_item_ids:
            menu_item = all_menu_items.get(menu_item_id)
            if not menu_item or not menu_item.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Позиция {menu_item_id} недоступна"
                )

        # Рассчитать цены
        items_with_price = []
        total_price = Decimal('0.00')
        for item in order_data.items:
            menu_item = all_menu_items[item.menu_item_id]
            item_price = (menu_item.base_price * multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            line_total = (item_price * item.quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            items_with_price.append((menu_item, item.quantity, item_price, line_total))
            total_price += line_total

        # 4. Применить лояльность
        discount_percent = Decimal('0.0')
        points_multiplier = Decimal('1.0')
        discount_amount = Decimal('0.0')
        redeem_used = 0
        points_earned = 0
        card = None
        
        if order_data.card_id:
            result = await db_session.execute(
                select(LoyaltyCard).where(LoyaltyCard.id == order_data.card_id)
            )
            card = result.scalar_one_or_none()
            if not card:
                raise HTTPException(status_code=404, detail="Card not found")
            
            if card.user_id and card.user_id != current_user.id and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to use this loyalty card"
                )
        
            # get_tier_discount возвращает TierDetailsResponse, извлекаем значения
            tier_info = await get_tier_discount(db_session, card)
            discount_percent = Decimal(str(tier_info.discount_percent))
            points_multiplier = Decimal(str(tier_info.points_multiplier))
            
            available_points = card.points_balance
            points_to_redeem = order_data.redeem_points or 0
            final_price, discount_amount, redeem_used = calculate_final_price(
                total_price,
                discount_percent,
                min(points_to_redeem, available_points)
            )
        else:
            final_price = total_price
        
        # 5. Проверить и зарезервировать ингредиенты
        item_tuples = [(mi.id, qty) for mi, qty, _, _ in items_with_price]
        await check_and_reserve_stock(db_session, item_tuples)

        # 6. Создать заказ и позиции
        order = Order(
            card_id=order_data.card_id if order_data.card_id else None,
            total_price=total_price,
            discount_applied=discount_amount,
            final_price=final_price,
            status='confirmed',
            points_earned=0  # пока 0, обновим после
        )
        db_session.add(order)
        await db_session.flush()

        for menu_item, qty, item_price, line_total in items_with_price:
            db_session.add(OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=qty,
                item_price_at_time=item_price
            ))

        # 7. Обновить карту лояльности и записать points_earned в заказ
        if card:
            card.points_balance -= redeem_used
            points_earned = int(float(final_price) * float(points_multiplier))
            card.points_balance += points_earned
            await recalc_tier(db_session, card)
            
            # Обновляем points_earned в заказе
            order.points_earned = points_earned
        # 8. Собрать items для ответа (конвертируем Decimal в float)
        order_items = [
            OrderItemResponse(
                menu_item_id=mi.id,
                name=mi.name,
                quantity=qty,
                item_price=float(item_price),
                total_line=float(line_total)
            )
            for mi, qty, item_price, line_total in items_with_price
        ]

        return OrderResponse(
            id=order.id,
            items=order_items,
            total_price=float(total_price),
            discount_applied=float(discount_amount),
            final_price=float(final_price),
            points_earned=points_earned,
            status=order.status,
            created_at=order.created_at
        )

