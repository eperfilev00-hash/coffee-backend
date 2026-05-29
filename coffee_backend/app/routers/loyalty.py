from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import LoyaltyCard
from coffee_backend.app.services.loyalty_services import get_tier_discount
from coffee_backend.app.schemas import LoyaltyCardResponse, RedeemRequest, RedeemResponse

router = APIRouter()

@router.get('/loyalty/cards/{card_id}', response_model=LoyaltyCardResponse)
async def loyalty_card_details(card_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LoyaltyCard).where(LoyaltyCard.id == card_id))
    detail = result.scalar_one_or_none()
    
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty Card Not Found")
    
    tier_details = await get_tier_discount(db, detail)
    
    return LoyaltyCardResponse(
        card_id=detail.id,
        customer_name=detail.customer_name,
        points_balance=detail.points_balance,
        tier=detail.tier,
        tier_details=tier_details
    )

@router.post('/loyalty/redeem', response_model=RedeemResponse)
async def redeem_point(data: RedeemRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LoyaltyCard).where(LoyaltyCard.id == data.card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty Card Not Found")
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