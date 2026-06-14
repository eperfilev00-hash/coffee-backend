from fastapi import HTTPException, status

# Базовый класс для всех бизнес-исключений
class AppError(HTTPException):
    """Базовый класс для всех бизнес-исключений приложения"""
    def __init__(self, status_code: int, detail: str, error_code: str | None = None, headers: dict | None = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or self.__class__.__name__

class NotFoundError(AppError):
    """Исключение когда ресурс не найден"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} с ID {identifier} не найден",
            error_code="NOT_FOUND"
        )


class InsufficientStockError(AppError):
    """Исключение когда недостаточно ингредиентов"""
    def __init__(self, missing_items: list):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Недостаточно ингредиентов",
            error_code="INSUFFICIENT_STOCK"
        )
        self.missing_items = missing_items


class ValidationError(AppError):
    """Исключение ошибки валидации бизнес-логики"""
    def __init__(self, errors: list):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ошибка валидации",
            error_code="VALIDATION_ERROR"
        )
        self.errors = errors


class DuplicateError(AppError):
    """Исключение дубликата записи"""
    def __init__(self, resource: str, field: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} с таким {field} уже существует",
            error_code="DUPLICATE_ENTRY"
        )

class UnauthorizedError(AppError):
    """Исключение неавторизованного пользователя"""
    def __init__(self, message: str | None = None, with_bearer: bool = True):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message or 'Не удалось подтвердить учетные данные',
            error_code="UNAUTHORIZED",
            headers={'WWW-Authenticate': 'Bearer'} if with_bearer else None,
        )
class ForbiddenError(AppError):
    """Проверка активного пользователя"""
    def __init__(self, message: str | None = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message or "Нет доступа к данным",
            error_code="FORBIDDEN",
        )