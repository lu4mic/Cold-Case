"""PostgreSQL-backed scenario test for the case API."""

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


async def test_case_routes_as_one_player_scenario(
    monkeypatch: MonkeyPatch,
) -> None:
    """Read a case, discover evidence, and keep other case data protected."""

    database_url = cast(str, TEST_DATABASE_URL)
    database_engine = create_database_engine(database_url)
    session_factory = create_session_factory(database_engine)
    mystery = make_case()
    other_mystery = make_case()
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

    async with database_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory.begin() as session:
        await create_case(session, mystery)
        await create_case(session, other_mystery)

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

            discovered_clue = mystery.clues[1]
            discovery_response = await client.post(
                f"/cases/{mystery.id}/clues/{discovered_clue.id}/discover"
            )
            discovered_clues_response = await client.get(
                f"/cases/{mystery.id}/clues"
            )
            discovered_state_response = await client.get(
                f"/cases/{mystery.id}/state"
            )
            repeated_discovery_response = await client.post(
                f"/cases/{mystery.id}/clues/{discovered_clue.id}/discover"
            )
            repeated_state_response = await client.get(
                f"/cases/{mystery.id}/state"
            )
            missing_clue_response = await client.post(
                f"/cases/{mystery.id}/clues/{uuid4()}/discover"
            )
            missing_case_discovery_response = await client.post(
                f"/cases/{uuid4()}/clues/{discovered_clue.id}/discover"
            )
            cross_case_response = await client.post(
                f"/cases/{mystery.id}/clues/"
                f"{other_mystery.clues[0].id}/discover"
            )
            other_clues_response = await client.get(
                f"/cases/{other_mystery.id}/clues"
            )
            other_state_response = await client.get(
                f"/cases/{other_mystery.id}/state"
            )

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
        assert discovery_response.status_code == 200
        assert discovery_response.json() == {
            "id": str(discovered_clue.id),
            "title": discovered_clue.title,
            "description": discovered_clue.description,
            "location": discovered_clue.location,
            "relevance": discovered_clue.relevance,
        }
        assert discovered_clues_response.status_code == 200
        assert [
            clue["id"] for clue in discovered_clues_response.json()
        ] == [str(mystery.clues[0].id), str(discovered_clue.id)]
        assert discovered_state_response.status_code == 200
        assert discovered_state_response.json()["discovered_clue_ids"] == [
            str(discovered_clue.id)
        ]
        assert repeated_discovery_response.status_code == 200
        assert repeated_discovery_response.json() == discovery_response.json()
        assert repeated_state_response.status_code == 200
        assert repeated_state_response.json()["discovered_clue_ids"] == [
            str(discovered_clue.id)
        ]
        assert missing_clue_response.status_code == 404
        assert missing_clue_response.json() == {"detail": "Clue not found"}
        assert missing_case_discovery_response.status_code == 404
        assert missing_case_discovery_response.json() == {"detail": "Case not found"}
        assert cross_case_response.status_code == 404
        assert cross_case_response.json() == {"detail": "Clue not found"}
        assert other_clues_response.status_code == 200
        assert other_clues_response.json() == []
        assert other_state_response.status_code == 200
        assert other_state_response.json()["discovered_clue_ids"] == []

        public_payloads = [
            case_response.json(),
            discovered_state_response.json(),
            *suspects_response.json(),
            *discovered_clues_response.json(),
        ]
        exposed_fields = set().union(
            *(payload.keys() for payload in public_payloads)
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

        assert exposed_fields.isdisjoint(forbidden_fields)
    finally:
        async with session_factory.begin() as session:
            await session.execute(
                delete(CaseTable).where(
                    CaseTable.id.in_([mystery.id, other_mystery.id])
                )
            )
        await database_engine.dispose()
