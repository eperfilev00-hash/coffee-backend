from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException, status
from sqlalchemy import select
from coffee_backend.app.models.models import LoyaltyCard, LoyaltyTier
from coffee_backend.app.schemas import TierDetailsResponse


async def get_tier_discount(db_session, card: LoyaltyCard) -> TierDetailsResponse:
    tier = await db_session.get(LoyaltyTier, card.tier)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некорректный tier карты: {card.tier}"
        )
    return TierDetailsResponse(
        discount_percent=float(tier.discount_percent),
        points_multiplier=float(tier.points_multiplier),
        min_points_for_tier=int(tier.min_points_for_tier)
    )

def calculate_final_price(
    total_price: Decimal,
    discount_percent: Decimal,
    redeem_points: int
) -> tuple[Decimal, Decimal, int]:
    discount_amount = (total_price * discount_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    price_after_discount = total_price - discount_amount
    redeem_value = min(redeem_points, int(price_after_discount))
    final_price = (price_after_discount - Decimal(redeem_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return final_price, discount_amount, redeem_value


async def recalc_tier(db_session, card: LoyaltyCard) -> None:
    if card.points_balance == 0:
        card.tier = 'bronze'
        return

    stmt = select(LoyaltyTier).order_by(LoyaltyTier.min_points_for_tier.desc())
    result = await db_session.execute(stmt)
    tiers = result.scalars().all()
    
    new_tier = None
    for tier in tiers:
        if card.points_balance >= tier.min_points_for_tier:
            new_tier = tier.tier_name
            break

    if new_tier:
        card.tier = new_tier
    else:
        card.tier = 'bronze'