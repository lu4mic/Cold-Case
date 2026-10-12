"""Run Alembic migrations against the configured PostgreSQL database."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from cold_case.database.tables import Base
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

fileConfig(context.config.config_file_name or "alembic.ini")
context.config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
target_metadata = Base.metadata


def configure_migrations(connection: Connection) -> None:
    """Configure Alembic with a live synchronous connection proxy."""

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations() -> None:
    """Create an async engine and execute pending migrations."""

    database_engine = async_engine_from_config(
        context.config.get_section(context.config.config_ini_section) or {},
        prefix="sqlalchemy.",
        pool_pre_ping=True,
    )

    try:
        async with database_engine.connect() as connection:
            await connection.run_sync(configure_migrations)
    finally:
        await database_engine.dispose()


asyncio.run(run_migrations())
