from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from coffee_backend.app.models.models import PricingRule
from datetime import datetime

async def get_current_multiplier(db: AsyncSession) -> Decimal:
    now = datetime.now()
    day = now.weekday()
    time = now.time()
    stmt = select(PricingRule).where(
        PricingRule.day_of_week == day,
        PricingRule.start_time <= time,
        PricingRule.end_time > time
    ).limit(1)
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()
    if rule:
        return rule.multiplier  # тип Decimal
    return Decimal('1.0')