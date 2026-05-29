from decimal import Decimal
import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_serializer



# Создаём тип, который автоматически конвертирует Decimal в float при JSON-сериализации
# Кастомный сериализатор для Decimal (округление до 2 знаков)
DecimalAsFloat = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(round(x, 2)), return_type=float)
]



class MenuItemResponse(BaseModel):
    id: int
    name: str
    base_price: DecimalAsFloat
    current_price: DecimalAsFloat
    is_available: bool

    model_config = ConfigDict(from_attributes=True)

class MenuItemCreate(BaseModel):
    name: str
    base_price: DecimalAsFloat
    is_available: bool

class MenuItemCreateResponse(BaseModel):
    id: int
    name: str
    base_price: DecimalAsFloat
    is_available: bool

    model_config = ConfigDict(from_attributes=True)

class OrderItemRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(gt=0)


class OrderCreateRequest(BaseModel):
    items: List[OrderItemRequest]
    card_id: Optional[int] = None
    redeem_points: Optional[int] = Field(default=0, ge=0)


class OrderItemResponse(BaseModel):
    menu_item_id: int
    name: str
    quantity: int
    item_price: float
    total_line: float

class OrderResponse(BaseModel):
    id: int
    items: List[OrderItemResponse]
    total_price: float
    discount_applied: float
    final_price: float
    points_earned: int
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class TierDetailsResponse(BaseModel):
    discount_percent: float
    points_multiplier: float
    min_points_for_tier: int

class LoyaltyCardResponse(BaseModel):
    card_id: int
    customer_name: str
    points_balance: int
    tier: str
    tier_details: TierDetailsResponse

    model_config = ConfigDict(from_attributes=True)

class LoyaltyCardCreate(BaseModel):
    customer_name:str
    initial_points:int

class RedeemResponse(BaseModel):
    success: bool
    redeemed_points: int
    remaining_balance: int

class RedeemRequest(BaseModel):
    card_id: int
    points: int = Field(gt=0)

class PricingRuleCreate(BaseModel):
    day_of_week: int
    start_time: datetime.time
    end_time: datetime.time
    multiplier: Decimal

class PricingRuleResponse(BaseModel):
    id: int
    day_of_week: int
    start_time: datetime.time
    end_time: datetime.time
    multiplier: DecimalAsFloat
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('start_time', 'end_time')
    def serialize_time(self, value: datetime.time):
        return value.strftime('%H:%M:%S')

class IngredientCreate(BaseModel):
    name:str
    stock_quantity:Decimal
    unit:str
    low_stock_threshold:int

class IngredientResponse(BaseModel):
    id: int
    name: str
    stock_quantity: DecimalAsFloat
    unit: str
    low_stock_threshold: DecimalAsFloat
    
    model_config = ConfigDict(from_attributes=True)

class IngredientQuantity(BaseModel):
    ingredient_id: int
    quantity: DecimalAsFloat

class RecipeCreate(BaseModel):
    menu_item_id: int
    ingredients: List[IngredientQuantity]

class RecipeContent(BaseModel):
    ingredient_id: int
    quantity_used: DecimalAsFloat

class RecipeResponse(BaseModel):
    menu_item_id: int
    ingredients: List[RecipeContent]
    
    model_config = ConfigDict(from_attributes=True)


