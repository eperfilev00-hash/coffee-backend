from decimal import Decimal
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coffee_backend.app.auth.dependencies import get_current_superuser
from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import Ingredient, LoyaltyCard, MenuItem, PricingRule, Recipe, User
from coffee_backend.app.schemas import (
    IngredientCreate, IngredientResponse, 
    LoyaltyCardCreate, LoyaltyCardResponse, 
    MenuItemCreate, MenuItemCreateResponse, 
    PricingRuleCreate, PricingRuleResponse, 
    RecipeCreate, RecipeResponse
)
from coffee_backend.app.services.loyalty_services import get_tier_discount, recalc_tier

router = APIRouter(tags=['Админ панель'], dependencies=[Depends(get_current_superuser)])

#Все маршруты теперь защищены get_current_superuser через dependencies

@router.post('/admin/menu/items', status_code=status.HTTP_201_CREATED, response_model=MenuItemCreateResponse)
async def create_position(
    item_data: MenuItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание пункта меню (только админ)."""
    new_item = MenuItem(
        name=item_data.name,
        base_price=item_data.base_price,
        is_available=item_data.is_available
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.post('/admin/recipes', status_code=status.HTTP_201_CREATED, response_model=RecipeResponse)
async def create_recipe(
    recipe: RecipeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание рецепта (только админ)."""
    menu_item_result = await db.execute(select(MenuItem).where(MenuItem.id == recipe.menu_item_id))
    menu_item = menu_item_result.scalars().first()
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item does not exist")
    
    for ing_data in recipe.ingredients:
        ingredient_result = await db.execute(select(Ingredient).where(Ingredient.id == ing_data.ingredient_id))
        ingredient = ingredient_result.scalar_one_or_none()
        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Ingredient with id {ing_data.ingredient_id} does not exist"
            )
        
        new_recipe = Recipe(
            menu_item_id=recipe.menu_item_id,
            ingredient_id=ing_data.ingredient_id,
            quantity_used=ing_data.quantity
        )
        db.add(new_recipe)
    
    await db.commit()
    
    recipe_items = [
        {"ingredient_id": ing.ingredient_id, "quantity_used": ing.quantity}
        for ing in recipe.ingredients
    ]
    return {
        "menu_item_id": recipe.menu_item_id,
        "ingredients": recipe_items
    }


@router.post('/admin/ingredients/new', response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredients(
    ingredient: IngredientCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание ингредиента (только админ)."""
    new_ingredient = Ingredient(
        name=ingredient.name,
        stock_quantity=ingredient.stock_quantity,
        unit=ingredient.unit,
        low_stock_threshold=ingredient.low_stock_threshold
    )
    db.add(new_ingredient)
    await db.commit()
    await db.refresh(new_ingredient)
    return new_ingredient


@router.post('/admin/ingredients/{ingredient_id}/stock', status_code=status.HTTP_200_OK)
async def check_stock(
    quantity: Decimal,
    ingredient_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Обновление остатков ингредиента (только админ)."""
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item does not exist")
    
    previous_quantity = ingredient.stock_quantity
    new_quantity = quantity + previous_quantity
    ingredient.stock_quantity = new_quantity
    await db.commit()
    await db.refresh(ingredient)
    
    return {
        "name": ingredient.name,
        "previous_quantity": float(previous_quantity),
        "new_quantity": float(ingredient.stock_quantity),
        "unit": ingredient.unit
    }


@router.post('/admin/pricing-rules', status_code=status.HTTP_201_CREATED, response_model=PricingRuleResponse)
async def create_pricing_rule(
    rule: PricingRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание правила ценообразования (только админ)."""
    new_rule = PricingRule(
        day_of_week=rule.day_of_week,
        start_time=rule.start_time,
        end_time=rule.end_time,
        multiplier=rule.multiplier
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule


@router.post('/admin/loyalty-cards', status_code=status.HTTP_201_CREATED, response_model=LoyaltyCardResponse)
async def create_loyalty_card(
    data_card: LoyaltyCardCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание карты лояльности (только админ)."""
    new_card = LoyaltyCard(
        customer_name=data_card.customer_name,
        points_balance=data_card.initial_points
    )
    db.add(new_card)
    await db.commit()
    await db.refresh(new_card)

    await recalc_tier(db, new_card)
    await db.commit()
    await db.refresh(new_card)

    tier_details = await get_tier_discount(db, new_card)
    return LoyaltyCardResponse(
        card_id=new_card.id,
        customer_name=new_card.customer_name,
        points_balance=new_card.points_balance,
        tier=new_card.tier,
        tier_details=tier_details
    )


# ⚡ Дополнительные админские операции для управления пользователями

@router.get('/admin/users', response_model=list[dict])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка всех пользователей (только админ)."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at
        }
        for user in users
    ]


@router.patch('/admin/users/{user_id}/status')
async def update_user_status(
    user_id: int,
    is_active: bool,
    db: AsyncSession = Depends(get_db)
):
    """Активация/деактивация пользователя (только админ)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_active = is_active
    await db.commit()
    
    return {"detail": f"User {user_id} {'activated' if is_active else 'deactivated'}"}