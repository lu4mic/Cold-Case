"""Pydantic models for application data."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""

    return datetime.now(UTC)


class GameStatus(StrEnum):
    """Possible states of a playable case."""

    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class MessageRole(StrEnum):
    """Authors allowed in an interrogation conversation."""

    PLAYER = "player"
    SUSPECT = "suspect"


class Suspect(BaseModel):
    """A person the player can investigate and interrogate."""

    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    name: str
    role: str
    personality: str
    motive: str
    public_background: str
    private_knowledge: list[str] = Field(default_factory=list)
    secret: str
    lie_strategy: str
    is_culprit: bool = False


class Clue(BaseModel):
    """Evidence that can be discovered during an investigation."""

    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    title: str
    description: str
    location: str
    discovered: bool = False
    relevance: str
    related_suspect_ids: list[UUID] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    """An ordered event in the true case timeline."""

    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    order: int = Field(ge=0)
    description: str
    involved_suspect_ids: list[UUID] = Field(default_factory=list)
    hidden: bool = True


class PlayerState(BaseModel):
    """The player's progress and current knowledge for one case."""

    case_id: UUID
    discovered_clue_ids: list[UUID] = Field(default_factory=list)
    interrogated_suspect_ids: list[UUID] = Field(default_factory=list)
    accusation: UUID | None = None
    game_status: GameStatus = GameStatus.IN_PROGRESS


class ConversationMessage(BaseModel):
    """One message in an interrogation conversation."""

    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    suspect_id: UUID
    role: MessageRole
    content: str
    created_at: AwareDatetime = Field(default_factory=utc_now)


class Case(BaseModel):
    """A complete mystery and the hidden truth owned by the backend."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    introduction: str
    location: str
    victim_or_event: str
    culprit_id: UUID | None = None
    status: GameStatus = GameStatus.IN_PROGRESS
    created_at: AwareDatetime = Field(default_factory=utc_now)
    suspects: list[Suspect] = Field(default_factory=list)
    clues: list[Clue] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    player_state: PlayerState | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
