"""Deterministic policy enforcement tests."""

from app.models import ActionType, Decision, MessageType
from policy import PolicyDirective, PolicyEngine


def test_policy_override_is_applied_after_router() -> None:
    decision = Decision(
        message_id="m1",
        action=ActionType.NOTIFY,
        message_type=MessageType.UNKNOWN,
        reason="provider recommendation",
        confidence=0.9,
        provider="test",
        decision_version="test-v1",
        prompt_version="test-v1",
    )
    directive = PolicyDirective(
        forced_action=ActionType.MUTE,
        reasons=("spam_or_critical_risk_override",),
    )

    result = PolicyEngine().after_router(None, decision, directive)  # type: ignore[arg-type]

    assert result.action == ActionType.MUTE
    assert "Policy override" in result.reason
    assert result.confidence <= decision.confidence
