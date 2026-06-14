from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from coffee_backend.app.auth.dependencies import get_current_user
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import LoyaltyCard, User
from coffee_backend.app.services.loyalty_services import get_tier_discount
from coffee_backend.app.schemas import LoyaltyCardResponse, RedeemRequest, RedeemResponse

router = APIRouter(tags=["Лояльность"])


@router.get('/loyalty/cards/{card_id}', response_model=LoyaltyCardResponse)
async def loyalty_card_details(
    card_id: int,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Получение деталей карты лояльности (требуется аутентификация)."""
    result = await db.execute(select(LoyaltyCard).where(LoyaltyCard.id == card_id))
    detail = result.scalar_one_or_none()
    
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty Card Not Found")

    if detail.user_id and detail.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    tier_details = await get_tier_discount(db, detail)
    
    return LoyaltyCardResponse(
        card_id=detail.id,
        customer_name=detail.customer_name,
        points_balance=detail.points_balance,
        tier=detail.tier,
        tier_details=tier_details
    )


@router.post('/loyalty/redeem', response_model=RedeemResponse)
async def redeem_point(
    data: RedeemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Списание баллов лояльности (требуется аутентификация)."""
    result = await db.execute(select(LoyaltyCard).where(LoyaltyCard.id == data.card_id))
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty Card Not Found")
    
    # ⚠️ КРИТИЧЕСКАЯ ПРОВЕРКА: только владелец карты или админ
    if card.user_id and card.user_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to redeem points for this card"
            )
    
    if data.points > card.points_balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid number of points to redeem")
    
    card.points_balance -= data.points
    await db.commit()
    await db.refresh(card)
    
    remaining_balance = card.points_balance
    
    return RedeemResponse(
        success=True,
        redeemed_points=data.points,
        remaining_balance=remaining_balance,
    )


@router.get('/loyalty/me', response_model=LoyaltyCardResponse)
async def get_my_loyalty_card(
    current_user: User = Depends(get_current_user),  
    db: AsyncSession = Depends(get_db)
):
    """Получение карты лояльности текущего пользователя."""
    if not current_user.loyalty_card:
        raise HTTPException(status_code=404, detail="Loyalty card not found for this user")
    
    tier_details = await get_tier_discount(db, current_user.loyalty_card)
    
    return LoyaltyCardResponse(
        card_id=current_user.loyalty_card.id,
        customer_name=current_user.loyalty_card.customer_name,
        points_balance=current_user.loyalty_card.points_balance,
        tier=current_user.loyalty_card.tier,
        tier_details=tier_details
    )