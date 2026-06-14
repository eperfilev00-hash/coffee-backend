"""
Обработчики глобальных исключений с логированием.

Каждый обработчик логирует ошибку перед возвратом ответа клиенту.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

import structlog

from .exceptions import AppError, InsufficientStockError

logger = structlog.get_logger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Обработчик для всех бизнес-исключений.
    
    Логирует предупреждение с контекстом запроса.
    """
    logger.warning(
        "business_error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
        client_ip=_get_client_ip(request),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
            }
        }
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Обработчик ошибок валидации."""
    errors = []
    for error in exc.errors():
        # Преобразуем bytes в строку, если нужно
        input_data = error.get("input")
        if isinstance(input_data, bytes):
            try:
                input_data = input_data.decode("utf-8")
            except:
                input_data = str(input_data)
        
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
    status_code=422,
        content={
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Ошибка валидации данных",
            "details": errors
        }
    }
)

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Обработчик непредвиденных ошибок.
    
    Логирует полную информацию об ошибке с traceback.
    """
    logger.exception(
        "unhandled_exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
        client_ip=_get_client_ip(request),
        query_params=dict(request.query_params) if request.query_params else None,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Внутренняя ошибка сервера"
            }
        }
    )


async def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
    """
    Обработчик ошибки недостаточного количества ингредиентов.
    
    Логирует предупреждение с деталями отсутствующих ингредиентов.
    """
    logger.warning(
        "insufficient_stock",
        error_code=exc.error_code,
        missing_items=exc.missing_items,
        path=request.url.path,
        method=request.method,
        client_ip=_get_client_ip(request),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "missing_items": exc.missing_items
            }
        }
    )


def _get_client_ip(request: Request) -> str:
    """Извлекает IP клиента из запроса, учитывая прокси."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"