import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select
import os

os.environ["TESTING"] = "1"

# Используем PostgreSQL из .env или переменных окружения
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://myuser:mypassword@localhost:5432/testdb")


@pytest.fixture(scope="session")
def event_loop():
    """Создаёт event loop для тестов."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def engine():
    """Тестовый движок БД."""
    from coffee_backend.app.models.models import Base
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # ОЧИЩАЕМ И СОЗДАЁМ таблицы перед КАЖДЫМ тестом
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine):
    """Сессия БД для каждого теста без автоматического коммита."""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
    )
    
    session = async_session()
    yield session
    await session.close()


@pytest.fixture(scope="function")
async def test_user(db_session):
    """Создание тестового пользователя."""
    from coffee_backend.app.models.models import User, LoyaltyCard
    from coffee_backend.app.auth.hash import hash_password
    
    hashed_pw = await hash_password("testpass123")
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hashed_pw,
        is_active=True,
        is_superuser=False,
        control_question="test_q",
        answer=await hash_password("test_answer")
    )
    db_session.add(user)
    await db_session.flush()
    
    loyalty = LoyaltyCard(
        user_id=user.id,
        customer_name="testuser",
        points_balance=100,
        tier="bronze"
    )
    db_session.add(loyalty)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(loyalty)
    
    return user


@pytest.fixture(scope="function")
async def authenticated_client(db_session, test_user):
    """HTTP клиент с авторизацией."""
    from coffee_backend.app.main import app
    from coffee_backend.app.database import get_db
    from coffee_backend.app.models.models import Session
    import datetime
    
    # Создаём сессию для пользователя
    session = Session(
        user_id=test_user.id,
        session_id="test-session-id-12345",
        is_active=True,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    )
    db_session.add(session)
    await db_session.commit()
    
    # Переопределяем dependency get_db
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Настраиваем клиент с cookie
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, 
        base_url="http://test",
        cookies={"session_id": "test-session-id-12345"}
    ) as ac:
        yield ac, test_user
    
    # Очищаем overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(db_session):
    """HTTP клиент без авторизации."""
    from coffee_backend.app.main import app
    from coffee_backend.app.database import get_db
    
    # Переопределяем dependency get_db
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Очищаем overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def menu_items(db_session):
    """Тестовые пункты меню."""
    from coffee_backend.app.models.models import MenuItem
    from decimal import Decimal
    
    items = [
        MenuItem(
            name="Espresso",
            base_price=Decimal("150.00"),
            is_available=True
        ),
        MenuItem(
            name="Cappuccino",
            base_price=Decimal("200.00"),
            is_available=True
        ),
        MenuItem(
            name="Latte",
            base_price=Decimal("220.00"),
            is_available=True
        )
    ]
    
    for item in items:
        db_session.add(item)
    
    await db_session.commit()