import pyotp

def generate_top_secret() -> str:
    """Генерирует новый TOTP-секрет"""
    return pyotp.random_base32()

def generate_top_url(secret:str,email:str,issuer:str = 'CoffeApp') -> str:
    """Генерирует URI для QR-кода Google Authenticator"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email,issuer_name=issuer)

def verify_totp(secret: str, token: str, window: int = 1) -> bool:
    """Проверяет TOTP-код с допуском +-1 интервал (30 сек)"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=window)

def get_current_totp(secret: str) -> str:
    """Возвращает текущий TOTP-код (для тестирования)"""
    totp = pyotp.TOTP(secret)
    return totp.now()