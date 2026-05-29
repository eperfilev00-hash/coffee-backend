from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from coffee_backend.app.routers import admin, loyalty, menu, orders
from coffee_backend.app.exception.exception_handlers import (
    app_error_handler,
    insufficient_stock_handler,
    validation_error_handler,
    generic_exception_handler
)
from coffee_backend.app.exception.exceptions import AppError, InsufficientStockError

app = FastAPI()

app.include_router(menu.router, prefix='/api/v1')
app.include_router(orders.router, prefix='/api/v1')
app.include_router(loyalty.router,prefix='/api/v1')
app.include_router(admin.router,prefix='/api/v1')
# Регистрация обработчиков исключений
app.add_exception_handler(AppError, app_error_handler) # type: ignore
app.add_exception_handler(RequestValidationError, validation_error_handler) # type: ignore
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(InsufficientStockError, insufficient_stock_handler)  # type: ignore