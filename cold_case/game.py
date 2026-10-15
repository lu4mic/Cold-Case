"""Deterministic game rules."""


from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cold_case.database.queries import (
    get_case,
    save_clue_discovery,
    save_final_accusation,
)
from cold_case.models import Clue, GameStatus, PlayerState


class Game:
    """Apply deterministic game rules using application database sessions."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session_factory = session_factory

    async def discover_clue(
        self,
        case_id: UUID,
        clue_id: UUID,
    ) -> Clue | None:
        """Discover a clue owned by the case, or return None when it is absent."""

        async with self.session_factory.begin() as session:
            mystery = await get_case(session, case_id)

            clue = next(
                (clue for clue in mystery.clues if clue.id == clue_id),
                None,
            )

            if clue is None:
                return None

            if not clue.discovered:
                await save_clue_discovery(session, case_id, clue_id)
                clue.discovered = True

            return clue

    async def final_accusation(
        self,
        case_id: UUID,
        suspect_id: UUID,
    ) -> PlayerState | None:
        """Record the final accusation and return the backend-decided outcome."""

        async with self.session_factory.begin() as session:
            mystery = await get_case(session, case_id)

            suspect = next(
                (suspect for suspect in mystery.suspects if suspect.id == suspect_id),
                None,
            )

            if suspect is None:
                return None

            player_state = mystery.player_state or PlayerState(case_id=case_id)

            if player_state.accusation is not None:
                return player_state

            player_state.accusation = suspect.id
            player_state.game_status = (
                GameStatus.WON
                if suspect.id == mystery.culprit_id
                else GameStatus.LOST
            )
            await save_final_accusation(
                session,
                case_id,
                suspect.id,
                player_state.game_status,
            )

            return player_state
