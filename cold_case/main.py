"""Application entry point and lifetime management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from cold_case.database.connection import (
    check_database_connection,
    create_database_engine,
    create_session_factory,
)

REQUIRED_ENVIRONMENT_VARIABLES = ["DATABASE_URL", "OPENAI_API_KEY"]


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
        application.state.database_engine = database_engine
        application.state.session_factory = create_session_factory(database_engine)
        yield
    finally:
        await database_engine.dispose()


app = FastAPI(title="Cold Case", lifespan=lifespan)
