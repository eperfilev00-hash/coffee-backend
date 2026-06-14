from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import partial
import os
from fastapi import Request, HTTPException, status


class RateLimiter:
    def __init__(self):
        self.request_history: dict[str, list[datetime]] = defaultdict(list)
    
    def is_allowed(
        self, 
        client_ip: str, 
        max_requests: int, 
        window_seconds: int
    ) -> bool:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        
        self.request_history[client_ip] = [
            ts for ts in self.request_history[client_ip]
            if ts > window_start
        ]
        
        if len(self.request_history[client_ip]) >= max_requests:
            return False
        
        self.request_history[client_ip].append(now)
        return True
    def get_retry_after(self, client_ip: str, window_seconds: int) -> int:
        if not self.request_history[client_ip]:
            return 0
        
        oldest_request = min(self.request_history[client_ip])
        now = datetime.now(timezone.utc)
        retry_after = int(
            (oldest_request + timedelta(seconds=window_seconds) - now).total_seconds()
        )
        return max(0, retry_after)


# Глобальный экземпляр
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    max_requests: int,
    window_seconds: int
):
    """Внутренняя функция для проверки rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
        retry_after = rate_limiter.get_retry_after(client_ip, window_seconds)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Too many requests",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )


# Factory-функции для создания зависимостей с разными лимитами
def rate_limit_5_per_minute(request: Request):
    """5 запросов в минуту"""
    from fastapi import Depends
    return Depends(lambda r: check_rate_limit(r, 5, 60))


def rate_limit_3_per_minute(request: Request):
    """3 запроса в минуту"""
    from fastapi import Depends
    return Depends(lambda r: check_rate_limit(r, 3, 60))


def rate_limit_10_per_minute(request: Request):
    """10 запросов в минуту"""
    from fastapi import Depends
    return Depends(lambda r: check_rate_limit(r, 10, 60))


def rate_limit_30_per_minute(request: Request):
    """30 запросов в минуту"""
    from fastapi import Depends
    return Depends(lambda r: check_rate_limit(r, 30, 60))


# Прямые функции для использования в Depends
async def rate_limit_login(request: Request):
    """Лимит для логина: 5 запросов в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 5, 60)


async def rate_limit_registration(request: Request):
    """Лимит для регистрации: 3 запроса в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 3, 60)


async def rate_limit_forgot_password(request: Request):
    """Лимит для forgot-password: 3 запроса в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 3, 60)


async def rate_limit_verify_reset_code(request: Request):
    """Лимит для проверки кода: 5 запросов в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 5, 60)


async def rate_limit_reset_password(request: Request):
    """Лимит для сброса пароля: 3 запроса в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 3, 60)

async def rate_limit_totp(request: Request):
    """Лимит для TOTP: 10 запросов в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 10, 60)


async def rate_limit_refresh(request: Request):
    """Лимит для refresh: 30 запросов в минуту"""
    if os.getenv("TESTING") == "1":
        return  # Пропускаем rate limit в тестах
    await check_rate_limit(request, 30, 60)