"""Database engine and session configuration."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_database_engine(database_url: str) -> AsyncEngine:
    """Create the application's asynchronous PostgreSQL engine."""

    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(
    database_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create sessions that keep loaded values available after commits."""

    return async_sessionmaker(database_engine, expire_on_commit=False)


async def check_database_connection(database_engine: AsyncEngine) -> None:
    """Confirm PostgreSQL accepts a connection before the API starts."""

    async with database_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
