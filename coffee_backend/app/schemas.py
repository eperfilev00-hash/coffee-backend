from decimal import Decimal
import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, field_serializer



# Создаём тип, который автоматически конвертирует Decimal в float при JSON-сериализации
# Кастомный сериализатор для Decimal (округление до 2 знаков)
DecimalAsFloat = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(round(x, 2)), return_type=float)
]



class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    control_question:str
    answer:str 

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime.datetime

    
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    """Ответ для успешного входа без 2FA"""
    user: UserResponse
    
class Login2FARequired(BaseModel):
    """Ответ когда требуется 2FA"""
    temporary_token: str
    message: str = "2FA code required"

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password:str
    new_password:str

class ForgorPasswordRequest(BaseModel):
    email:EmailStr
    
class TOTPSetupRequest(BaseModel):
    """Запрос на настройку TOTP."""
    password: str  # Требует пароль для подтверждения

class TOTPSetupResponse(BaseModel):
    """Ответ с секретом и QR-кодом."""
    secret: str
    qr_uri: str
    manual_entry_code: str

class TOTPVerifyRequest(BaseModel):
    """Запрос на верификацию TOTP кода."""
    token: str

class EnableTOTPRequest(BaseModel):
    """Запрос на включение TOTP после верификации."""
    token: str  # Код для подтверждения при включении

class TOTPLoginRequest(BaseModel):
    """Запрос на вход с TOTP кодом (второй шаг)."""
    temporary_token: str  # Временный токен из первого шага
    totp_code: str

class ForgotPasswordRequest(BaseModel):
    """Запрос на инициацию сброса пароля."""
    email: EmailStr

class VerifyResetCodeRequest(BaseModel):
    """Запрос на проверку кода сброса."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')

class ResetPasswordRequest(BaseModel):
    """Запрос на сброс пароля после верификации."""
    token: str = Field(..., min_length=10)  # Токен из URL
    new_password: str = Field(..., min_length=8, max_length=128)

class ResetPasswordByCodeRequest(BaseModel):
    """Запрос на сброс пароля по коду."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    new_password: str = Field(..., min_length=8, max_length=128)

class ResetPasswordResponse(BaseModel):
    """Ответ на успешный сброс пароля."""
    success: bool
    message: str

class VerifyCodeResponse(BaseModel):
    """Ответ на проверку кода."""
    verified: bool
    message: str

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