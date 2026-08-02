"""Validation and safe fallback for Router decisions."""

from app.models import ActionType, Decision, DecisionPacket, MessageType
from pipeline.errors import DecisionValidationError


class ConfidenceValidator:
    """Validate confidence and measured execution fields."""

    def validate(self, decision: Decision) -> None:
        if not 0.0 <= decision.confidence <= 1.0:
            raise DecisionValidationError("confidence outside [0, 1]")
        if decision.latency_ms < 0 or decision.token_usage < 0 or decision.repair_count < 0:
            raise DecisionValidationError("execution metrics must be non-negative")


class EvidenceValidator:
    """Ensure every cited evidence message exists in the packet."""

    def validate(self, decision: Decision, packet: DecisionPacket) -> None:
        available = {
            item.source_message_id for item in packet.evidence.items if item.source_message_id
        }
        if any(identifier not in available for identifier in decision.evidence_message_ids):
            raise DecisionValidationError("decision cites unavailable evidence")


class DecisionValidator:
    """Validate complete decision schema and required metadata."""

    def __init__(self) -> None:
        self._confidence = ConfidenceValidator()
        self._evidence = EvidenceValidator()

    def validate(self, decision: Decision, packet: DecisionPacket) -> Decision:
        try:
            checked = Decision.model_validate(decision.model_dump())
            if checked.action not in tuple(ActionType) or checked.message_type not in tuple(
                MessageType
            ):
                raise DecisionValidationError("invalid action or message type")
            if not checked.prompt_version or not checked.decision_version or not checked.provider:
                raise DecisionValidationError("required decision metadata is missing")
            self._confidence.validate(checked)
            self._evidence.validate(checked, packet)
            return checked
        except DecisionValidationError:
            raise
        except Exception as error:
            raise DecisionValidationError("decision schema validation failed") from error


class ValidationEngine:
    """Public validation boundary with deterministic fallback."""

    def __init__(self, logger: object) -> None:
        self._validator = DecisionValidator()
        self._logger = logger

    def validate_or_fallback(self, decision: Decision, packet: DecisionPacket) -> Decision:
        try:
            return self._validator.validate(decision, packet)
        except DecisionValidationError as error:
            self._logger.warning("decision_validation_failed", error=str(error))  # type: ignore[attr-defined]
            return Decision(
                message_id=packet.context.message.message_id,
                action=ActionType.MUTE,
                message_type=MessageType.UNKNOWN,
                reason="Safe fallback: decision validation failed.",
                confidence=0.0,
                evidence_message_ids=(),
                provider="fallback",
                decision_version="phase8-v1",
                prompt_version="phase8-fallback-v1",
            )
