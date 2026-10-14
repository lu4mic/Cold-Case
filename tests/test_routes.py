"""PostgreSQL-backed scenario test for the read-only case API."""

import json
import os
from typing import cast
from uuid import uuid4

import pytest
from cold_case.database.connection import (
    create_database_engine,
    create_session_factory,
)
from cold_case.database.queries import create_case
from cold_case.database.tables import Base, CaseTable
from cold_case.main import app
from cold_case.models import Clue
from httpx import ASGITransport, AsyncClient
from pytest import MonkeyPatch
from sqlalchemy import delete

from tests.test_models import make_case

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is required for PostgreSQL route tests",
)


async def test_read_only_case_routes_as_one_player_scenario(
    monkeypatch: MonkeyPatch,
) -> None:
    """Store a case, read every public view, and verify hidden truth stays hidden."""

    database_url = cast(str, TEST_DATABASE_URL)
    database_engine = create_database_engine(database_url)
    session_factory = create_session_factory(database_engine)
    mystery = make_case()
    mystery.clues[0].discovered = True
    mystery.clues.append(
        Clue(
            case_id=mystery.id,
            title="Undiscovered ticket",
            description="A ticket hidden beneath a seat.",
            location="Passenger carriage",
            relevance="Connects a passenger to the final train.",
        )
    )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("OPENAI_API_KEY", "integration-test-key")

    async with database_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory.begin() as session:
        await create_case(session, mystery)

    try:
        async with app.router.lifespan_context(app), AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            health_response = await client.get("/health")
            case_response = await client.get(f"/cases/{mystery.id}")
            suspects_response = await client.get(f"/cases/{mystery.id}/suspects")
            clues_response = await client.get(f"/cases/{mystery.id}/clues")
            state_response = await client.get(f"/cases/{mystery.id}/state")
            missing_response = await client.get(f"/cases/{uuid4()}")

        assert health_response.status_code == 200
        assert health_response.json() == {"status": "ok"}
        assert case_response.status_code == 200
        assert case_response.json()["title"] == mystery.title
        assert suspects_response.status_code == 200
        assert len(suspects_response.json()) == len(mystery.suspects)
        assert clues_response.status_code == 200
        assert clues_response.json() == [
            {
                "id": str(mystery.clues[0].id),
                "title": mystery.clues[0].title,
                "description": mystery.clues[0].description,
                "location": mystery.clues[0].location,
                "relevance": mystery.clues[0].relevance,
            }
        ]
        assert state_response.status_code == 200
        assert state_response.json()["game_status"] == "in_progress"
        assert missing_response.status_code == 404
        assert missing_response.json() == {"detail": "Case not found"}

        serialized_responses = json.dumps(
            [
                case_response.json(),
                suspects_response.json(),
                clues_response.json(),
                state_response.json(),
            ]
        )
        forbidden_fields = {
            "culprit_id",
            "is_culprit",
            "motive",
            "private_knowledge",
            "secret",
            "lie_strategy",
            "timeline",
            "discovered",
            "related_suspect_ids",
        }

        assert all(
            forbidden_field not in serialized_responses
            for forbidden_field in forbidden_fields
        )
    finally:
        async with session_factory.begin() as session:
            await session.execute(delete(CaseTable).where(CaseTable.id == mystery.id))
        await database_engine.dispose()
