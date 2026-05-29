from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coffee_backend.app.database import get_db
from coffee_backend.app.models.models import Ingredient, LoyaltyCard, MenuItem, PricingRule, Recipe
from coffee_backend.app.schemas import IngredientCreate, IngredientResponse, LoyaltyCardCreate, LoyaltyCardResponse, MenuItemCreate, MenuItemCreateResponse, PricingRuleCreate, PricingRuleResponse, RecipeCreate, RecipeResponse
from coffee_backend.app.services.loyalty_services import get_tier_discount, recalc_tier

router = APIRouter()

@router.post('/admin/menu/items',status_code=status.HTTP_201_CREATED,response_model=MenuItemCreateResponse)
async def create_position(item_data: MenuItemCreate,db: AsyncSession = Depends(get_db)):
    new_item = MenuItem(     
        name=item_data.name,
        base_price=item_data.base_price,
        is_available=item_data.is_available
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@router.post('/admin/recipes',status_code=status.HTTP_201_CREATED,response_model=RecipeResponse)
async def create_recipe(recipe: RecipeCreate,db:AsyncSession = Depends(get_db)):
    menu_item_result = await db.execute(select(MenuItem).where(MenuItem.id == recipe.menu_item_id))
    menu_item = menu_item_result.scalars().first()
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Menu item does not exist")
    for ing_data in recipe.ingredients:
        ingredient_result = await db.execute(select(Ingredient).where(Ingredient.id == ing_data.ingredient_id))
        ingredient = ingredient_result.scalar_one_or_none()
        if not ingredient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ingredient with id {ing_data.ingredient_id} does not exist")
        
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

@router.post('/admin/ingredients/new',response_model=IngredientResponse,status_code=status.HTTP_201_CREATED)
async def create_ingredients(ingredient: IngredientCreate,db:AsyncSession = Depends(get_db)):
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

@router.post('/admin/ingredients/{ingredient_id}/stock',status_code=status.HTTP_200_OK)
async def check_stock(quantity:Decimal,ingredient_id:int, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ingredient).where(Ingredient.id == ingredient_id))
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Item does not exist")
    previous_quantity = ingredient.stock_quantity
    new_quantity = quantity + previous_quantity
    ingredient.stock_quantity = new_quantity
    await db.commit()
    await db.refresh(ingredient)
    return { 
        "name":ingredient.name,
        "previous_quantity": previous_quantity,
        "new_quantity": ingredient.stock_quantity,
        "unit": ingredient.unit
    }

@router.post('/admin/pricing-rules',status_code=status.HTTP_201_CREATED,response_model=PricingRuleResponse)
async def create_pricing_rule(rule: PricingRuleCreate,db:AsyncSession = Depends(get_db)):
    new_rule = PricingRule(
        day_of_week = rule.day_of_week,
        start_time = rule.start_time,
        end_time = rule.end_time,
        multiplier = rule.multiplier,
        )
    
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule

@router.post('/admin/loyalty-cards',status_code=status.HTTP_201_CREATED,response_model=LoyaltyCardResponse)
async def create_loyalty_card(data_card:LoyaltyCardCreate,db:AsyncSession = Depends(get_db)):
    new_card = LoyaltyCard(
        customer_name=data_card.customer_name,
        points_balance=data_card.initial_points
    )
    db.add(new_card)
    await db.commit()
    await db.refresh(new_card)

    await recalc_tier(db,new_card)
    await db.commit()
    await db.refresh(new_card)

    tier_details = await get_tier_discount(db,new_card)
    return LoyaltyCardResponse(
        card_id=new_card.id,
        customer_name=new_card.customer_name,
        points_balance=new_card.points_balance,
        tier=new_card.tier,
        tier_details=tier_details
    )