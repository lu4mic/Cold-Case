"""Create the initial Cold Case schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261012_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create cases and all case-owned records."""

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("introduction", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("victim_or_event", sa.Text(), nullable=False),
        sa.Column("culprit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "suspects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(120), nullable=False),
        sa.Column("personality", sa.Text(), nullable=False),
        sa.Column("motive", sa.Text(), nullable=False),
        sa.Column("public_background", sa.Text(), nullable=False),
        sa.Column("private_knowledge", postgresql.JSONB(), nullable=False),
        sa.Column("secret", sa.Text(), nullable=False),
        sa.Column("lie_strategy", sa.Text(), nullable=False),
        sa.Column("is_culprit", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_suspects_case_id", "suspects", ["case_id"])
    op.create_foreign_key(
        "fk_cases_culprit_id", "cases", "suspects", ["culprit_id"], ["id"]
    )
    op.create_table(
        "clues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("discovered", sa.Boolean(), nullable=False),
        sa.Column("relevance", sa.Text(), nullable=False),
        sa.Column("related_suspect_ids", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_clues_case_id", "clues", ["case_id"])
    op.create_table(
        "timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("involved_suspect_ids", postgresql.JSONB(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_timeline_events_case_id", "timeline_events", ["case_id"])
    op.create_table(
        "player_states",
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("discovered_clue_ids", postgresql.JSONB(), nullable=False),
        sa.Column("interrogated_suspect_ids", postgresql.JSONB(), nullable=False),
        sa.Column(
            "accusation",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suspects.id"),
            nullable=True,
        ),
        sa.Column("game_status", sa.String(30), nullable=False),
    )
    op.create_table(
        "conversation_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "suspect_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suspects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_conversation_messages_case_id", "conversation_messages", ["case_id"]
    )


def downgrade() -> None:
    """Remove the initial Cold Case schema."""

    op.drop_index(
        "ix_conversation_messages_case_id", table_name="conversation_messages"
    )
    op.drop_table("conversation_messages")
    op.drop_table("player_states")
    op.drop_index("ix_timeline_events_case_id", table_name="timeline_events")
    op.drop_table("timeline_events")
    op.drop_index("ix_clues_case_id", table_name="clues")
    op.drop_table("clues")
    op.drop_constraint("fk_cases_culprit_id", "cases", type_="foreignkey")
    op.drop_index("ix_suspects_case_id", table_name="suspects")
    op.drop_table("suspects")
    op.drop_table("cases")
