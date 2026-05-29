from sqlalchemy import select
from coffee_backend.app.models.models import Ingredient, Recipe
from coffee_backend.app.exception.exceptions import InsufficientStockError

async def check_and_reserve_stock(db_session, items: list[tuple[int, int]]) -> None:
    # items: [(menu_item_id, quantity), ...]
    # Собираем все ингредиенты, необходимые для заказа
    needed = {}
    for menu_id, qty in items:
        recipe_stmt = select(Recipe).where(Recipe.menu_item_id == menu_id)
        result = await db_session.execute(recipe_stmt)
        for rec in result.scalars():
            needed[rec.ingredient_id] = needed.get(rec.ingredient_id, 0) + rec.quantity_used * qty

    # Блокируем строки ингредиентов и проверяем остатки
    errors = []
    valid_ingredients = []  # храним (ing, required_qty)

    for ing_id, required_qty in sorted(needed.items()):
        stmt = select(Ingredient).where(Ingredient.id == ing_id).with_for_update()
        result = await db_session.execute(stmt)
        ing = result.scalar_one_or_none()

        if not ing or ing.stock_quantity < required_qty:
            errors.append({
                "ingredient_id": ing_id,
                "required": float(required_qty),
                "available": float(ing.stock_quantity) if ing else 0.0
            })

        else:
            valid_ingredients.append((ing, required_qty))

    if errors:
        raise InsufficientStockError(errors)

    # Теперь списываем
    for ing, required_qty in valid_ingredients:
        ing.stock_quantity -= required_qty
    # Явно не вызываем update, так как объект в сессии отслеживается, при flush обновится

