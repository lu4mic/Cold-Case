"""Deterministic game rules."""


from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cold_case.database.queries import get_case, save_clue_discovery
from cold_case.models import Clue


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
