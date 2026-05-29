from decimal import Decimal
from coffee_backend.app.models.models import (
    Ingredient,
    LoyaltyCard,
    LoyaltyTier,
    MenuItem,
    PricingRule,
    Recipe,
)


async def create_ingredient(
    session,
    name="Milk",
    stock_quantity=Decimal("1000"),
    unit="ml",
    low_stock_threshold=Decimal("50"),
):
    ing = Ingredient(
        name=name,
        stock_quantity=stock_quantity,
        unit=unit,
        low_stock_threshold=low_stock_threshold,
    )
    session.add(ing)
    await session.flush()
    await session.refresh(ing)
    return ing


async def create_menu_item(
    session,
    name="Latte",
    base_price=Decimal("5.00"),
    is_available=True,
):
    item = MenuItem(name=name, base_price=base_price, is_available=is_available)
    session.add(item)
    await session.flush()
    await session.refresh(item)
    return item


async def create_recipe(session, menu_item_id: int, ingredient_id: int, quantity_used: Decimal):
    recipe = Recipe(
        menu_item_id=menu_item_id,
        ingredient_id=ingredient_id,
        quantity_used=quantity_used,
    )
    session.add(recipe)
    await session.flush()
    return recipe


async def seed_loyalty_tiers(session):
    """Бронза/серебро/золото — обязательны для логики лояльности."""
    tiers = [
        LoyaltyTier(tier_name="bronze", discount_percent=Decimal("0"), points_multiplier=Decimal("1.00"), min_points_for_tier=0),
        LoyaltyTier(tier_name="silver", discount_percent=Decimal("5"), points_multiplier=Decimal("1.10"), min_points_for_tier=100),
        LoyaltyTier(tier_name="gold", discount_percent=Decimal("10"), points_multiplier=Decimal("1.20"), min_points_for_tier=500),
    ]
    session.add_all(tiers)
    await session.flush()


async def create_loyalty_card(session, customer_name="John Doe", points_balance=0, tier="bronze"):
    card = LoyaltyCard(customer_name=customer_name, points_balance=points_balance, tier=tier)
    session.add(card)
    await session.flush()
    await session.refresh(card)
    return card


async def create_pricing_rule(
    session,
    day_of_week=0,
    start_time=None,
    end_time=None,
    multiplier=Decimal("1.0"),
):
    from datetime import time
    rule = PricingRule(
        day_of_week=day_of_week,
        start_time=start_time or time(0, 0),
        end_time=end_time or time(23, 59),
        multiplier=multiplier,
    )
    session.add(rule)
    await session.flush()
    await session.refresh(rule)
    return rule