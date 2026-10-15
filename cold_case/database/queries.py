"""Database read and write operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cold_case.database.tables import (
    CaseTable,
    ClueTable,
    ConversationMessageTable,
    PlayerStateTable,
    SuspectTable,
    TimelineEventTable,
)
from cold_case.models import (
    Case,
    Clue,
    ConversationMessage,
    GameStatus,
    MessageRole,
    PlayerState,
    Suspect,
    TimelineEvent,
)


async def create_case(session: AsyncSession, mystery: Case) -> None:
    """Add a complete case to the current transaction."""

    player_state = mystery.player_state or PlayerState(case_id=mystery.id)
    stored_case = CaseTable(
        id=mystery.id,
        title=mystery.title,
        introduction=mystery.introduction,
        location=mystery.location,
        victim_or_event=mystery.victim_or_event,
        culprit_id=None,
        status=mystery.status.value,
        created_at=mystery.created_at,
        suspects=[
            SuspectTable(
                id=suspect.id,
                case_id=mystery.id,
                name=suspect.name,
                role=suspect.role,
                personality=suspect.personality,
                motive=suspect.motive,
                public_background=suspect.public_background,
                private_knowledge=suspect.private_knowledge,
                secret=suspect.secret,
                lie_strategy=suspect.lie_strategy,
                is_culprit=suspect.is_culprit,
            )
            for suspect in mystery.suspects
        ],
        clues=[
            ClueTable(
                id=clue.id,
                case_id=mystery.id,
                title=clue.title,
                description=clue.description,
                location=clue.location,
                discovered=clue.discovered,
                relevance=clue.relevance,
                related_suspect_ids=[
                    str(suspect_id) for suspect_id in clue.related_suspect_ids
                ],
            )
            for clue in mystery.clues
        ],
        timeline=[
            TimelineEventTable(
                id=event.id,
                case_id=mystery.id,
                order=event.order,
                description=event.description,
                involved_suspect_ids=[
                    str(suspect_id) for suspect_id in event.involved_suspect_ids
                ],
                hidden=event.hidden,
            )
            for event in mystery.timeline
        ],
        player_state=PlayerStateTable(
            case_id=mystery.id,
            discovered_clue_ids=[
                str(clue_id) for clue_id in player_state.discovered_clue_ids
            ],
            interrogated_suspect_ids=[
                str(suspect_id) for suspect_id in player_state.interrogated_suspect_ids
            ],
            accusation=player_state.accusation,
            game_status=player_state.game_status.value,
        ),
    )
    session.add(stored_case)
    await session.flush()
    session.add_all(
        [
            ConversationMessageTable(
                id=message.id,
                case_id=mystery.id,
                suspect_id=message.suspect_id,
                role=message.role.value,
                content=message.content,
                created_at=message.created_at,
            )
            for message in mystery.messages
        ]
    )
    await session.flush()
    stored_case.culprit_id = mystery.culprit_id
    await session.flush()


async def save_clue_discovery(
    session: AsyncSession,
    case_id: UUID,
    clue_id: UUID,
) -> None:
    """Persist one clue discovery in the current transaction."""

    stored_clue = (
        await session.execute(
            select(ClueTable).where(
                ClueTable.id == clue_id,
                ClueTable.case_id == case_id,
            )
        )
    ).scalar_one()
    stored_player_state = (
        await session.execute(
            select(PlayerStateTable).where(PlayerStateTable.case_id == case_id)
        )
    ).scalar_one()
    discovered_clue_id = str(clue_id)

    stored_clue.discovered = True

    if discovered_clue_id not in stored_player_state.discovered_clue_ids:
        stored_player_state.discovered_clue_ids = [
            *stored_player_state.discovered_clue_ids,
            discovered_clue_id,
        ]

    await session.flush()


async def save_final_accusation(
    session: AsyncSession,
    case_id: UUID,
    suspect_id: UUID,
    game_status: GameStatus,
) -> None:
    """Persist one final accusation and its backend-decided outcome."""

    stored_case = (
        await session.execute(select(CaseTable).where(CaseTable.id == case_id))
    ).scalar_one()
    stored_player_state = (
        await session.execute(
            select(PlayerStateTable).where(PlayerStateTable.case_id == case_id)
        )
    ).scalar_one()

    stored_case.status = game_status.value
    stored_player_state.accusation = suspect_id
    stored_player_state.game_status = game_status.value

    await session.flush()


async def get_case(session: AsyncSession, case_id: UUID) -> Case:
    """Load one complete case or raise when its ID does not exist."""

    stored_case = (
        await session.execute(
            select(CaseTable)
            .where(CaseTable.id == case_id)
            .options(
                selectinload(CaseTable.suspects),
                selectinload(CaseTable.clues),
                selectinload(CaseTable.timeline),
                selectinload(CaseTable.player_state),
                selectinload(CaseTable.messages),
            )
        )
    ).scalar_one()

    return Case(
        id=stored_case.id,
        title=stored_case.title,
        introduction=stored_case.introduction,
        location=stored_case.location,
        victim_or_event=stored_case.victim_or_event,
        culprit_id=stored_case.culprit_id,
        status=GameStatus(stored_case.status),
        created_at=stored_case.created_at,
        suspects=[
            Suspect(
                id=suspect.id,
                case_id=suspect.case_id,
                name=suspect.name,
                role=suspect.role,
                personality=suspect.personality,
                motive=suspect.motive,
                public_background=suspect.public_background,
                private_knowledge=suspect.private_knowledge,
                secret=suspect.secret,
                lie_strategy=suspect.lie_strategy,
                is_culprit=suspect.is_culprit,
            )
            for suspect in stored_case.suspects
        ],
        clues=[
            Clue(
                id=clue.id,
                case_id=clue.case_id,
                title=clue.title,
                description=clue.description,
                location=clue.location,
                discovered=clue.discovered,
                relevance=clue.relevance,
                related_suspect_ids=[
                    UUID(suspect_id) for suspect_id in clue.related_suspect_ids
                ],
            )
            for clue in stored_case.clues
        ],
        timeline=[
            TimelineEvent(
                id=event.id,
                case_id=event.case_id,
                order=event.order,
                description=event.description,
                involved_suspect_ids=[
                    UUID(suspect_id) for suspect_id in event.involved_suspect_ids
                ],
                hidden=event.hidden,
            )
            for event in stored_case.timeline
        ],
        player_state=PlayerState(
            case_id=stored_case.player_state.case_id,
            discovered_clue_ids=[
                UUID(clue_id)
                for clue_id in stored_case.player_state.discovered_clue_ids
            ],
            interrogated_suspect_ids=[
                UUID(suspect_id)
                for suspect_id in stored_case.player_state.interrogated_suspect_ids
            ],
            accusation=stored_case.player_state.accusation,
            game_status=GameStatus(stored_case.player_state.game_status),
        ),
        messages=[
            ConversationMessage(
                id=message.id,
                case_id=message.case_id,
                suspect_id=message.suspect_id,
                role=MessageRole(message.role),
                content=message.content,
                created_at=message.created_at,
            )
            for message in stored_case.messages
        ],
    )
