"""Phase 1 domain contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.models import (
    ActionType,
    ConfidenceScore,
    ConversationType,
    Decision,
    DecisionTrace,
    MediaType,
    Message,
    MessageType,
    OutputFile,
    OutputRow,
    Timestamp,
)


def test_message_round_trips_through_json() -> None:
    """A core model can serialize and deserialize without losing enums."""
    message = Message(
        message_id="msg_1",
        user_id="user_1",
        conversation_id="conversation_1",
        conversation_type=ConversationType.PERSONAL,
        created_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        media_type=MediaType.IMAGE,
    )

    restored = Message.model_validate_json(message.model_dump_json())
    assert restored == message
    assert restored.media_type is MediaType.IMAGE


def test_models_are_immutable() -> None:
    """Frozen domain objects cannot be mutated after validation."""
    row = OutputRow(
        message_id="msg_1",
        action=ActionType.NOTIFY,
        message_type=MessageType.PERSONAL,
        reason="contract test",
        confidence=0.5,
        evidence_message_ids="none",
    )

    with pytest.raises(PydanticValidationError):
        row.action = ActionType.MUTE  # type: ignore[misc]


def test_naive_timestamps_are_rejected() -> None:
    """All domain timestamps must carry timezone information."""
    with pytest.raises(PydanticValidationError):
        Message(
            message_id="msg_1",
            user_id="user_1",
            conversation_id="conversation_1",
            conversation_type=ConversationType.PERSONAL,
            created_at=datetime(2026, 8, 1, 12, 0),
        )


def test_enum_and_score_constraints_are_enforced() -> None:
    """Enums and normalized score bounds reject invalid input."""
    with pytest.raises(PydanticValidationError):
        OutputRow(
            message_id="msg_1",
            action="later",  # type: ignore[arg-type]
            message_type=MessageType.UNKNOWN,
            reason="invalid action",
            confidence=0.5,
            evidence_message_ids="none",
        )
    with pytest.raises(PydanticValidationError):
        Decision(
            message_id="msg_1",
            action=ActionType.DIGEST,
            message_type=MessageType.UNKNOWN,
            confidence=1.1,
        )


def test_output_file_and_trace_are_serializable() -> None:
    """Aggregate output and trace models expose JSON schema and JSON output."""
    output = OutputFile(
        rows=(
            OutputRow(
                message_id="msg_1",
                action=ActionType.DIGEST,
                message_type=MessageType.EVENT,
                reason="contract test",
                confidence=0.75,
                evidence_message_ids="none",
            ),
        )
    )
    decision = Decision(
        message_id="msg_1",
        action=ActionType.DIGEST,
        message_type=MessageType.EVENT,
        confidence=0.75,
        trace=DecisionTrace(steps=("validated",)),
    )

    assert output.model_dump(mode="json")["rows"][0]["action"] == "digest"
    assert "properties" in OutputFile.model_json_schema()
    assert decision.trace.steps == ("validated",)


def test_reusable_value_objects_are_pydantic_validated() -> None:
    """Reusable aliases retain their constraints in TypeAdapter validation."""
    from pydantic import TypeAdapter

    assert TypeAdapter(ConfidenceScore).validate_python(0.25) == 0.25
    assert TypeAdapter(Timestamp).validate_python(datetime.now(UTC)).tzinfo is not None
    with pytest.raises(PydanticValidationError):
        TypeAdapter(ConfidenceScore).validate_python(-0.01)
