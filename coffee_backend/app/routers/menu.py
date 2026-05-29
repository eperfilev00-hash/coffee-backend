from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import MenuItem
from coffee_backend.app.schemas import MenuItemResponse
from coffee_backend.app.services.pricing import get_current_multiplier

router = APIRouter()

@router.get("/menu", response_model=list[MenuItemResponse],status_code=status.HTTP_200_OK)
async def get_menu(db: AsyncSession = Depends(get_db)):
    multiplier = await get_current_multiplier(db)
    stmt = select(MenuItem).where(MenuItem.is_available == True)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return [
        MenuItemResponse(
            id=item.id,
            name=item.name,
            base_price=item.base_price,
            current_price = (item.base_price * multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            is_available=item.is_available,
        )
        for item in items
    ]