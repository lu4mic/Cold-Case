"""SQLAlchemy table mappings for PostgreSQL."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Metadata base used by SQLAlchemy and Alembic."""


class CaseTable(Base):
    """Stored mystery and its backend-owned truth."""

    __tablename__ = "cases"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(String(200))
    introduction: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200))
    victim_or_event: Mapped[str] = mapped_column(Text)
    culprit_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("suspects.id", name="fk_cases_culprit_id", use_alter=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), default="in_progress")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    suspects: Mapped[list["SuspectTable"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        foreign_keys="SuspectTable.case_id",
    )
    clues: Mapped[list["ClueTable"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    timeline: Mapped[list["TimelineEventTable"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="TimelineEventTable.order",
    )
    player_state: Mapped["PlayerStateTable"] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    messages: Mapped[list["ConversationMessageTable"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="ConversationMessageTable.created_at",
    )


class SuspectTable(Base):
    """Stored suspect including private game information."""

    __tablename__ = "suspects"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    case_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(120))
    personality: Mapped[str] = mapped_column(Text)
    motive: Mapped[str] = mapped_column(Text)
    public_background: Mapped[str] = mapped_column(Text)
    private_knowledge: Mapped[list[str]] = mapped_column(JSONB, default=list)
    secret: Mapped[str] = mapped_column(Text)
    lie_strategy: Mapped[str] = mapped_column(Text)
    is_culprit: Mapped[bool] = mapped_column(Boolean, default=False)

    case: Mapped[CaseTable] = relationship(
        back_populates="suspects", foreign_keys=[case_id]
    )


class ClueTable(Base):
    """Stored discoverable evidence."""

    __tablename__ = "clues"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    case_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200))
    discovered: Mapped[bool] = mapped_column(Boolean, default=False)
    relevance: Mapped[str] = mapped_column(Text)
    related_suspect_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)

    case: Mapped[CaseTable] = relationship(back_populates="clues")


class TimelineEventTable(Base):
    """Stored event in the true ordered case timeline."""

    __tablename__ = "timeline_events"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    case_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
    )
    order: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    involved_suspect_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    hidden: Mapped[bool] = mapped_column(Boolean, default=True)

    case: Mapped[CaseTable] = relationship(back_populates="timeline")


class PlayerStateTable(Base):
    """Stored investigation progress for one case."""

    __tablename__ = "player_states"

    case_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    discovered_clue_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    interrogated_suspect_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    accusation: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("suspects.id"), nullable=True
    )
    game_status: Mapped[str] = mapped_column(String(30), default="in_progress")

    case: Mapped[CaseTable] = relationship(back_populates="player_state")


class ConversationMessageTable(Base):
    """Stored interrogation message."""

    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    case_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        index=True,
    )
    suspect_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("suspects.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    case: Mapped[CaseTable] = relationship(back_populates="messages")
