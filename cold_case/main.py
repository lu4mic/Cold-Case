"""Application entry point and lifetime management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import NoResultFound

from cold_case.database.connection import (
    check_database_connection,
    create_database_engine,
    create_session_factory,
)
from cold_case.game import Game
from cold_case.routers import cases, health

REQUIRED_ENVIRONMENT_VARIABLES = ["DATABASE_URL"]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
    """Verify configuration and manage database resources."""

    missing_environment_variables = [
        environment_variable
        for environment_variable in REQUIRED_ENVIRONMENT_VARIABLES
        if environment_variable not in os.environ
    ]

    if missing_environment_variables:
        raise ValueError(
            "Missing required environment variables: "
            f"{', '.join(missing_environment_variables)}"
        )

    database_engine = create_database_engine(os.environ["DATABASE_URL"])

    try:
        await check_database_connection(database_engine)
        session_factory = create_session_factory(database_engine)
        application.state.database_engine = database_engine
        application.state.session_factory = session_factory
        application.state.game = Game(session_factory)
        yield
    finally:
        await database_engine.dispose()


app = FastAPI(title="Cold Case", lifespan=lifespan)


@app.exception_handler(NoResultFound)
async def case_not_found(
    request: Request,
    error: NoResultFound,
) -> JSONResponse:
    """Translate a missing database case into a public HTTP response."""

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Case not found"},
    )


app.include_router(cases.router)
app.include_router(health.router)
