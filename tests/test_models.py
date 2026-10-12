"""Tests for the Pydantic application models."""

from uuid import uuid4

from cold_case.models import (
    Case,
    Clue,
    ConversationMessage,
    MessageRole,
    PlayerState,
    Suspect,
    TimelineEvent,
)


def make_case() -> Case:
    """Build a small valid case for model tests."""

    case_id = uuid4()
    culprit_id = uuid4()
    witness_id = uuid4()
    clue_id = uuid4()

    return Case(
        id=case_id,
        title="The Last Train from Blackwood",
        introduction="A railway inspector vanished during the final journey.",
        location="Blackwood railway line",
        victim_or_event="The disappearance of a railway inspector",
        culprit_id=culprit_id,
        suspects=[
            Suspect(
                id=culprit_id,
                case_id=case_id,
                name="Alex Vale",
                role="Passenger",
                personality="Guarded",
                motive="Avoid exposure",
                public_background="Travelled on the final train.",
                private_knowledge=["Heard an argument."],
                secret="Entered the luggage car.",
                lie_strategy="Minimize involvement.",
                is_culprit=True,
            ),
            Suspect(
                id=witness_id,
                case_id=case_id,
                name="Morgan Reed",
                role="Conductor",
                personality="Direct",
                motive="Protect the railway's reputation",
                public_background="Worked aboard the final train.",
                secret="Ignored a safety procedure.",
                lie_strategy="Redirect questions toward railway policy.",
            ),
        ],
        clues=[
            Clue(
                id=clue_id,
                case_id=case_id,
                title="Broken watch",
                description="The watch stopped shortly after midnight.",
                location="Inspector's compartment",
                relevance="Establishes the likely time of the incident.",
                related_suspect_ids=[culprit_id],
            )
        ],
        timeline=[
            TimelineEvent(
                case_id=case_id,
                order=1,
                description="The inspector entered the compartment.",
                involved_suspect_ids=[culprit_id],
            )
        ],
        player_state=PlayerState(case_id=case_id),
        messages=[
            ConversationMessage(
                case_id=case_id,
                suspect_id=witness_id,
                role=MessageRole.PLAYER,
                content="Where were you at midnight?",
            )
        ],
    )


def test_complete_case_is_valid() -> None:
    mystery = make_case()

    assert mystery.culprit_id == mystery.suspects[0].id
    assert mystery.created_at.tzinfo is not None
    assert mystery.player_state is not None
    assert mystery.player_state.discovered_clue_ids == []


def test_case_has_safe_defaults() -> None:
    mystery = Case(
        title="The Empty Compartment",
        introduction="A locked train compartment was found empty.",
        location="Blackwood station",
        victim_or_event="A missing passenger",
    )

    assert mystery.culprit_id is None
    assert mystery.suspects == []
    assert mystery.clues == []
    assert mystery.timeline == []
    assert mystery.player_state is None
    assert mystery.messages == []
