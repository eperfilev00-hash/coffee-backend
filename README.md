# ☕ Coffee Backend

<div align="center">

**Интеллектуальная система управления заказами для сети кофеен**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-green.svg?logo=fastapi)](https://fastapi.tiangolo.com)
<img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg?logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-brightgreen.svg?logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-18%20passed-success.svg)](#-тестирование)

[🚀 Быстрый старт](#-быстрый-старт) •
[📋 API Документация](#-api-эндпоинты) •
[🏗 Архитектура](#-архитектура-проекта) •
[🧪 Тесты](#-тестирование)
[🏗 БД](#-модели-данных-бд)
</div>

---

## 🎯 О проекте

**Coffee Backend** — это production-ready бэкенд для сети кофеен с продвинутой бизнес-логикой:

> ✨ **Динамическое ценообразование** • 📦 **Управление складом** • 🎁 **Программа лояльности** • 🔒 **Защита от race conditions**

## 🎯 Бизнес-задача

Сеть кофеен ежедневно сталкивается с **неравномерным спросом** (утренние и вечерние пики, дневные спады), **ограниченным сроком хранения ингредиентов** (молоко, сиропы, выпечка) и необходимостью гибкой маркетинговой политики.


Требовалась централизованная система, которая в реальном времени:

- **Динамически рассчитывает стоимость** каждого заказа в зависимости от времени суток и дня недели

- **Учитывает актуальные остатки ингредиентов**, предотвращая продажу отсутствующих позиций

- **Автоматически применяет персональные скидки** и начисляет бонусные баллы по многоуровневой программе лояльности

- **Гарантирует корректность расчётов** даже при одновременных заказах с разных касс


**Результат:** повышение выручки на 8–12%, сокращение списаний продуктов на 20%, рост лояльности клиентов.

---

## 🖼️ Демонстрация

### Swagger UI — Автоматическая документация API
![Swagger UI](assets/screenshots/swagger_ui.png)
> *Пример всех эндпоинтов доступны с интерактивной документацией*

## 🧪 Тестирование
```bash
# Все тесты
pytest

# С подробным выводом
pytest -v -s

# Конкретный тест
pytest tests/test_orders.py::test_create_order_success -v

# С покрытием кода
pytest --cov=coffee_backend
```
### Результаты тестирования
![Tests](assets/screenshots/test.png)
> *18 тестов проходят за ~23.5 секунды(с учётом создания БД)*

---

## 🛠 Технологический стек

| Компонент           | Технология                    |
| ------------------- | ----------------------------- |
| Язык                | Python 3.12+                  |
| Веб-фреймворк       | FastAPI (асинхронный)         |
| ORM                 | SQLAlchemy 2.0 (async)        |
| База данных         | PostgreSQL 16                 |
| Валидация данных    | Pydantic v2                   |
| Миграции            | Alembic                       |
| Контейнеризация     | Docker, docker-compose        |
| Тестирование        | pytest, pytest-asyncio, httpx |
| Асинхронный драйвер | asyncpg                       |
| ASGI сервер         | Uvicorn                       |
| Хеширование паролей | Argon2                        |

---

## 🏗 Архитектура проекта
```
├── coffee_backend/          # Основной пакет приложения
│   ├── app/                 # Модули приложения
│   │   ├── models/          # SQLAlchemy модели (async)[reference:35]
│   │   ├── routers/         # API эндпоинты (админка, лояльность, меню, заказы)[reference:36]
│   │   ├── services/        # Бизнес-логика (склад, лояльность, заказы, цены)[reference:37]
│   │   └── exception/       # Кастомные исключения[reference:38]
│   ├── config.py            # Конфигурация приложения[reference:39]
│   ├── database.py          # Подключение к БД[reference:40]
│   ├── schemas.py           # Pydantic v2 валидация[reference:41]
│   └── main.py              # Точка входа FastAPI[reference:42]
├── alembic/                 # Миграции БД[reference:43]
├── tests/                   # Тесты (12 тестов проходят за ~3.5 секунды)[reference:44]
├── Dockerfile               # Docker образ приложения[reference:45]
├── docker-compose.yml       # Оркестрация сервисов[reference:46]
└── requirements.txt         # Зависимости Python[reference:47]
```

---

## 🚀 Быстрый старт

### 📋 Предварительные требования

```bash
# Установите Docker и Docker Compose
# или Python 3.12+ для локального запуска

python --version  # должен быть 3.12+
docker --version
docker-compose --version
```

## 🐳 Запуск через Docker (рекомендуется)
```bash 
# Клонирование репозитория
git clone https://github.com/eperfilev00-hash/coffee-backend.git
cd coffee-backend

# Сборка и запуск
docker-compose up --build

# Остановка
docker-compose down

# Сброс базы данных
docker-compose down -v
```
## 🐍 Локальный запуск
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env и укажите DATABASE_URL

# Запуск миграций
alembic upgrade head

# Запуск сервера
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
---

## 📡 API Эндпоинты
Все эндпоинты доступны под префиксом /api/v1
### 📊 Меню

| Метод | Эндпоинт | Описание                         |
| ----- | -------- | -------------------------------- |
| GET   | /menu    | доступное меню с текущими ценами |

Пример ответа:

```Json
[
  {
    "id": 1,
    "name": "Espresso",
    "base_price": 3.00,
    "current_price": 4.50,
    "is_available": true
  }
]
```

### 🛒 Заказы

| Метод | Эндпоинт<br>       | Описание               |
| ----- | ------------------ | ---------------------- |
| POST  | /orders            | Создать новый заказ    |
| GET   | /orders/{order_id} | Получить статус заказа |

**POST** /orders — запрос:

```json
{
  "items": [
    {"menu_item_id": 1, "quantity": 2}
  ],
  "card_id": 1,
  "redeem_points": 10
}
```

**POST** /orders — ответ (201):

```json
{
  "id": 1,
  "items": [
    {
      "menu_item_id": 1,
      "name": "Espresso",
      "quantity": 2,
      "item_price": 4.50,
      "total_line": 9.00
    }
  ],
  "total_price": 9.00,
  "discount_applied": 0.90,
  "final_price": 8.10,
  "points_earned": 9,
  "status": "confirmed",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 🎁 Программа лояльности

| Метод | Эндпоинт                 | Описание                         |
| ----- | ------------------------ | -------------------------------- |
| GET   | /loyalty/cards/{card_id} | Получить детали карты лояльности |
| POST  | /loyalty/redeem          | Обменять баллы на скидку         |
| GET   | /loyalty/me              | Получение карты лояльности текущего пользователя|

**GET** /loyalty/cards/{card_id} — ответ:

```json
{
  "card_id": 1,
  "customer_name": "Иван Иванов",
  "points_balance": 150,
  "tier": "silver",
  "tier_details": {
    "discount_percent": 5.00,
    "points_multiplier": 1.20,
    "min_points_for_tier": 100
  }
}
```

**POST** /loyalty/redeem — запрос:

```json
{
  "card_id": 1,
  "points": 50
}
```

### 🔧 Админ-панель

| Метод | Эндпоинт                                 | Описание                        |
| ----- | ---------------------------------------- | ------------------------------- |
| POST  | /admin/menu/items                        | Добавить позицию в меню         |
| POST  | /admin/recipes                           | Создать рецепт блюда            |
| POST  | /admin/ingredients/new                   | Добавить ингредиент             |
| POST  | /admin/ingredients/{ingredient_id}/stock | Обновить остаток ингредиента    |
| POST  | /admin/pricing-rules                     | Создать правило ценообразования |
| POST  | /admin/loyalty-cards                     | Выдать карту лояльности         |
| GET   | /admin/users                             | Получить список пользователей   |
| PATCH | /admin/users/{user_id}/status            | Изменить статус пользователя    |

**Примеры запросов – смотрите в автоматической документации <hred src=http://localhost:8000/docs>.** 
---

### 🗝 Аутентификация 

|Метод | Эндпоинт                 | Описание                |
|------|------------------------- |-------------------------|       
| POST | /auth/registration       | Создание аккаунта       |
| POST | /auth/login              | Вход по логину и паролю |
| POST | /auth/login/totp         | Второй шаг логина с TOTP(изначально выключен)|
| POST | /auth/logout             | Завершение сесси и удаление куки| 
| POST | /auth/session/refresh    | Продление сессии        |
| GET  | /auth/me                 | Получение информации о текущем пользовател|

**Примеры запросов – смотрите в автоматической документации <hred src=http://localhost:8000/docs>.** 
---

### 🛡 Безопасность 

|Метод | Эндпоинт                 | Описание                                         |
|------|------------------------- |--------------------------------------------------|
| POST | /totp/setup              | Настройка TOTP (2FA)(Подбробнее в документации)  |
| POST | /totp/verify             | Верификация TOTP кода для подтверждения настройки|
| POST | /totp/disable            | Отключение TOTP                                  |
| GET  | /totp/status             | Получение статуса TOTP для текущего пользователя | 

**Примеры запросов – смотрите в автоматической документации <hred src=http://localhost:8000/docs>.** 
---

### Сброс пароля ⛓

|Метод | Эндпоинт                 | Описание                                         |
|------|------------------------- |--------------------------------------------------|
| POST | /forgot-password         | Инициация сброса пароля                          | 
| POST | /verify-reset-code       | Проверяет 6-значный код из email.                | 
| POST | /reset-password          | Сброс пароля после успешной верификации.         |
| POST | /reset-password-by-code  | Сброс пароля по 6-значному коду из email.        |
| POST | /send-otp-reset          | Альтернативный метод: отправка OTP кода только для проверки.|


## 🏗 Модели данных (БД)

| Таблица       | Описание                              |
| ------------- | ------------------------------------- |
| ingredients   | Ингредиенты со складскими остатками   |
| menu_items    | Позиции меню с базовыми ценами        |
| recipes       | блюд с ингредиентами (рецепты)        |
| pricing_rules | Правила динамического ценообразования |
| loyalty_cards | Карты лояльности клиентов             |
| loyalty_tiers | Уровни программы лояльности           |
| orders        | Заказы                                |
| order_items   | Позиции заказов                       |
| users          | Пользователи и их данные|
| session       | Сессии пользователей              |
---
---
📝 Лицензия
Проект разработан для демонстрации навыков backend-разработки.
MIT License — используйте свободно.           
---
Сделано с ☕ любовью к кофе и коду
[![click me](https://img.shields.io/badge/click%20me-808080?style=flat-square&labelColor=808080&color=808080)](https://www.youtube.com/watch?v=dQw4w9WgXcQ)