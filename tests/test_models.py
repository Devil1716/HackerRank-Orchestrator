"""Unit tests for domain boundary validation."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.constants import Action, ConversationType, MessageType
from app.models import Decision, Message, OutputRow


def test_message_rejects_negative_forward_count() -> None:
    """Reject invalid non-negative fields at the domain boundary."""
    with pytest.raises(ValidationError):
        Message(
            message_id="msg_1",
            user_id="u_1",
            conversation_type=ConversationType.PERSONAL,
            created_at=datetime.now(UTC),
            forwarded_count=-1,
        )


def test_output_row_uses_contract_enums() -> None:
    """Serialize enum values as the challenge contract expects."""
    row = OutputRow(
        message_id="msg_1",
        action=Action.NOTIFY,
        message_type=MessageType.PERSONAL,
        reason="reserved for a future decision service",
        confidence=0.5,
        evidence_message_ids="none",
    )
    assert row.action == "notify"


def test_decision_validates_confidence() -> None:
    """Reject confidence values outside the closed unit interval."""
    with pytest.raises(ValidationError):
        Decision(
            message_id="msg_1",
            action=Action.MUTE,
            message_type=MessageType.UNKNOWN,
            reason="invalid confidence",
            confidence=1.1,
        )
