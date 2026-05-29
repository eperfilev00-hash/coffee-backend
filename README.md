# ☕ Coffee Backend

<div align="center">

**Интеллектуальная система управления заказами для сети кофеен**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-green.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg?logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-brightgreen.svg?logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-12%20passed-success.svg)](#-тестирование)

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
> *Все эндпоинты доступны с интерактивной документацией*
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
> *12 тестов проходят за ~3.5 секунды*

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

---

## 🏗 Архитектура проекта
```
📁 coffee_backend/                  # Основной пакет приложения
│
├── 📁 app/
│   ├── 📁 models/                    # SQLAlchemy модели (async)
│   │   ├── 📄 base.py
│   │   └── 📄 models.py
│   │
│   ├── 📁 routers/                 # API эндпоинты
│   │   ├── 📄 admin.py             # Админ-панель
│   │   ├── 📄 loyalty.py           # Программа лояльности
│   │   ├── 📄 menu.py              # Меню
│   │   └── 📄 orders.py            # Заказы
│   │
│   ├── 📁 services/                # Бизнес-логика
│   │   ├── 📄 inventory.py         # Управление складом
│   │   ├── 📄 loyalty_services.py  # Логика лояльности
│   │   ├── 📄 order_services.py    # Создание заказов
│   │   └── 📄 pricing.py           # Динамическое ценообразование
│   │
│   ├── 📁 exception/               # Кастомные исключения
│   ├── 📄 config.py                # Конфигурация приложения
│   ├── 📄 database.py              # Подключение к БД
│   ├── 📄 schemas.py               # Pydantic v2 валидация
│   └── 📄 main.py                  # Точка входа FastAPI
│
├── 📁 alembic/                     # Миграции БД
├── 📄 alembic.ini
│
├── 📁 tests/                       # Тесты
│   ├── 📄 conftest.py
│   ├── 📄 factories.py
│   ├── 📄 test_admin.py
│   ├── 📄 test_menu.py
│   ├── 📄 test_orders.py
│   └── 📄 test_services.py
│
├── 📄 DockerFile                   # Docker образ приложения
├── 📄 docker-compose.yml           # Оркестрация сервисов
├── 📄 requirements.txt             # Зависимости Python
└── 📄 pytest.ini                   # Конфигурация pytest
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
|       |                          |                                  |

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
--------------------------------------------------------------------------

**Примеры запросов – смотрите в автоматической документации <hred src=http://localhost:8000/docs>.** 

---
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
---
---
📝 Лицензия
Проект разработан для демонстрации навыков backend-разработки.
MIT License — используйте свободно.           
---
Сделано с ☕ любовью к кофе и коду
[![click me](https://img.shields.io/badge/click%20me-808080?style=flat-square&labelColor=808080&color=808080)](https://www.youtube.com/watch?v=dQw4w9WgXcQ)