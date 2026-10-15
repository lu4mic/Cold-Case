"""HTTP routes."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from cold_case.database.queries import get_case
from cold_case.models import PublicCase, PublicClue, PublicPlayerState, PublicSuspect
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


async def database_session(request: Request) -> AsyncGenerator[AsyncSession]:
    """Provide one database session for the current request."""

    async with request.app.state.session_factory.begin() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(database_session)]


@router.get("/{case_id}", response_model=PublicCase, status_code=status.HTTP_200_OK)
async def find_case(case_id: UUID, session: DatabaseSession) -> PublicCase:
    """Return the player-safe information for one stored case."""

    mystery = await get_case(session, case_id)

    return PublicCase.model_validate(mystery)


@router.get(
    "/{case_id}/suspects",
    response_model=list[PublicSuspect],
    status_code=status.HTTP_200_OK,
)
async def find_suspects(case_id: UUID, session: DatabaseSession) -> list[PublicSuspect]:
    mystery = await get_case(session, case_id)

    return [PublicSuspect.model_validate(suspect) for suspect in mystery.suspects]


@router.get(
    "/{case_id}/clues", response_model=list[PublicClue], status_code=status.HTTP_200_OK
)
async def find_clues(case_id: UUID, session: DatabaseSession) -> list[PublicClue]:
    mystery = await get_case(session, case_id)

    return [
        PublicClue.model_validate(clue) for clue in mystery.clues if clue.discovered
    ]


@router.get(
    "/{case_id}/state", response_model=PublicPlayerState, status_code=status.HTTP_200_OK
)
async def find_case_state(case_id: UUID, session: DatabaseSession) -> PublicPlayerState:
    mystery = await get_case(session, case_id)

    return PublicPlayerState.model_validate(mystery.player_state)


@router.post(
    "/{case_id}/clues/{clue_id}/discover",
    response_model=PublicClue,
    status_code=status.HTTP_200_OK,
)
async def find_case_clue(
    case_id: UUID,
    clue_id: UUID,
    request: Request,
) -> PublicClue:
    clue = await request.app.state.game.discover_clue(case_id, clue_id)

    if clue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clue not found",
        )

    return PublicClue.model_validate(clue)

@router.post(
    "/{case_id}/accuse/{suspect_id}",
    response_model=PublicPlayerState,
    status_code=status.HTTP_200_OK,
)
async def accuse_suspect(
    case_id: UUID,
    suspect_id: UUID,
    request: Request,
) -> PublicPlayerState:
    player_state = await request.app.state.game.final_accusation(case_id, suspect_id)

    if player_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suspect not found",
        )

    return PublicPlayerState.model_validate(player_state)
