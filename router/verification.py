"""Deterministic post-router consistency verification."""

from dataclasses import dataclass

from app.models import ActionType, Decision, DecisionPacket
from policy.engine import PolicyEngine
from router.errors import InvalidDecisionError


@dataclass(frozen=True)
class VerificationResult:
    """Verified decision and any deterministic corrections applied."""

    decision: Decision
    corrections: tuple[str, ...] = ()


class DecisionVerifier:
    """Check provider output against packet evidence and high-risk signals."""

    def verify(self, decision: Decision, packet: DecisionPacket) -> VerificationResult:
        """Return a verified decision or raise for an unrecoverable contradiction."""
        if not decision.reason.strip():
            raise InvalidDecisionError("decision reason must not be empty")
        available = {
            item.source_message_id for item in packet.evidence.items if item.source_message_id
        }
        if any(identifier not in available for identifier in decision.evidence_message_ids):
            raise InvalidDecisionError("decision cites evidence absent from the packet")

        corrections: list[str] = []
        corrected = decision
        if (
            decision.action == ActionType.NOTIFY
            and PolicyEngine.is_explicit_scam(packet)
            and packet.signals.spam.value >= 0.85
        ):
            corrected = decision.model_copy(
                update={
                    "action": ActionType.MUTE,
                    "reason": "Deterministic verifier override: high spam risk. " + decision.reason,
                    "confidence": min(decision.confidence, packet.signals.spam.value),
                }
            )
            corrections.append("notify_to_mute_high_spam")

        return VerificationResult(decision=corrected, corrections=tuple(corrections))
