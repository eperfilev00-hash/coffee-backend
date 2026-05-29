from logging.config import fileConfig
from sqlalchemy import pool
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
from coffee_backend.app.config import settings

import os
import sys

# Добавляем родительскую директорию (backend/) в sys.path
# __file__ = coffee_backend/alembic/env.py
# dirname(__file__) = coffee_backend/alembic/
# dirname(dirname(__file__)) = coffee_backend/
# dirname(dirname(dirname(__file__))) = backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from coffee_backend.app.models.base import Base
import coffee_backend.app.models.models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()