from sqlalchemy import create_engine

from coffee_backend.app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_= AsyncSession
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session