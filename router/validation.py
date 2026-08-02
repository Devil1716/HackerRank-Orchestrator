"""Structured output parsing, validation, repair, and retry."""

import json

from app.models import Decision, DecisionPacket
from router.contracts import Provider, ProviderResponse
from router.errors import InvalidDecisionError


class DecisionParser:
    """Parse strict JSON into the existing immutable Decision model."""

    def parse(
        self,
        content: str,
        packet: DecisionPacket,
        provider: str,
        tokens: int,
        latency_ms: float,
        repairs: int,
    ) -> Decision:
        try:
            data = json.loads(content)
            return Decision.model_validate(
                {
                    **data,
                    "message_id": packet.context.message.message_id,
                    "provider": provider,
                    "latency_ms": latency_ms,
                    "token_usage": tokens,
                    "repair_count": repairs,
                }
            )
        except (ValueError, TypeError, KeyError) as error:
            raise InvalidDecisionError("provider output is not valid Decision JSON") from error


class SchemaValidator:
    """Validate parser output and action/message enums through Pydantic."""

    def validate(self, decision: Decision) -> Decision:
        return Decision.model_validate(decision.model_dump())


class RepairEngine:
    """Perform one explicit structured-output repair attempt."""

    def repair(self, provider: Provider, content: str) -> ProviderResponse:
        return provider.complete(
            "Repair this output into strict JSON with action, message_type, reason, confidence, evidence_message_ids: "
            + content
        )


class RetryPolicy:
    """Bound retries to one repair attempt."""

    max_repairs = 1
