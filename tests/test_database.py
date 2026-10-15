"""Scenario tests for database configuration and application lifetime."""

from unittest.mock import AsyncMock, Mock

from cold_case import main
from cold_case.database.connection import (
    create_database_engine,
    create_session_factory,
)
from fastapi import FastAPI
from pytest import MonkeyPatch, raises
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class FakeDatabaseEngine:
    """Track application cleanup without opening a real connection."""

    disposed = False

    async def dispose(self) -> None:
        """Record that application shutdown released the engine."""

        self.disposed = True


async def test_database_configuration_and_application_lifetime(
    monkeypatch: MonkeyPatch,
) -> None:
    """Require a database, start without an AI key, and release resources."""

    database_url = "postgresql+psycopg://detective:secret@localhost/test_case"
    fake_database_engine = FakeDatabaseEngine()
    connection_check = AsyncMock()
    session_factory = object()
    application = FastAPI(lifespan=main.lifespan)

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with raises(
        ValueError,
        match="Missing required environment variables: DATABASE_URL$",
    ):
        async with application.router.lifespan_context(application):
            raise AssertionError("startup unexpectedly accepted missing variables")

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setattr(
        main,
        "create_database_engine",
        Mock(return_value=fake_database_engine),
    )
    monkeypatch.setattr(
        main,
        "create_session_factory",
        Mock(return_value=session_factory),
    )
    monkeypatch.setattr(main, "check_database_connection", connection_check)

    connection_check.side_effect = ConnectionError("PostgreSQL unavailable")
    with raises(ConnectionError, match="PostgreSQL unavailable"):
        async with application.router.lifespan_context(application):
            raise AssertionError("startup unexpectedly ignored the database failure")

    assert fake_database_engine.disposed is True

    fake_database_engine.disposed = False
    connection_check.reset_mock(side_effect=True)

    async with application.router.lifespan_context(application):
        assert application.state.database_engine is fake_database_engine
        assert application.state.session_factory is session_factory
        connection_check.assert_awaited_once_with(fake_database_engine)

    assert fake_database_engine.disposed is True


async def test_database_builders_use_async_psycopg() -> None:
    """Build the real engine and session factory without opening PostgreSQL."""

    database_engine = create_database_engine(
        "postgresql+psycopg://postgres:postgres@localhost:5432/cold_case"
    )
    session_factory = create_session_factory(database_engine)

    assert isinstance(database_engine, AsyncEngine)
    assert database_engine.url.drivername == "postgresql+psycopg"
    assert isinstance(session_factory, async_sessionmaker)
    assert session_factory.class_ is AsyncSession

    await database_engine.dispose()
