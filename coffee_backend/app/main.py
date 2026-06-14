from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from coffee_backend.app.routers import admin, loyalty, menu, orders, auth, password, security
from coffee_backend.app.exception.exception_handlers import (
    app_error_handler,
    insufficient_stock_handler,
    validation_error_handler,
    generic_exception_handler
)
from coffee_backend.app.exception.exceptions import AppError, InsufficientStockError


app = FastAPI(
    title="Coffee Backend API",
    description="Интеллектуальная система управления заказами для сети кофеен",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# Подключение router'ов
app.include_router(password.router, prefix='/api/v1') 
app.include_router(security.router,prefix='/api/v1')
app.include_router(auth.router, prefix='/api/v1/auth')  
app.include_router(menu.router, prefix='/api/v1')
app.include_router(orders.router, prefix='/api/v1')
app.include_router(loyalty.router, prefix='/api/v1')
app.include_router(admin.router, prefix='/api/v1')

# Обработчики исключений
app.add_exception_handler(AppError, app_error_handler) # type: ignore
app.add_exception_handler(RequestValidationError, validation_error_handler) # type: ignore
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(InsufficientStockError, insufficient_stock_handler) # type: ignore

@app.get("/")
async def root():
    return {"message": "Coffee Backend API", "docs": "/docs"}

