"""Phase 6.75 Decision Orchestrator."""

from time import perf_counter
from uuid import uuid4

import structlog

from app.models import (
    DecisionFeatures,
    DecisionPacket,
    DecisionSignals,
    EvidenceBundle,
    ExecutionMetadata,
    MessageContext,
    PersonalizationProfile,
)
from orchestration.builders import DecisionPacketFactory, TraceBuilder
from orchestration.errors import DecisionPacketInputError
from orchestration.validators import DecisionPacketValidator


class DecisionPacketBuilder:
    """Build a packet from the five deterministic pipeline outputs."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def build(
        self,
        context: MessageContext,
        personalization: PersonalizationProfile,
        evidence: EvidenceBundle,
        features: DecisionFeatures,
        signals: DecisionSignals,
    ) -> DecisionPacket:
        """Build and validate a complete immutable packet."""
        started = perf_counter()
        now = context.timestamps.context_built_at
        stages = (
            TraceBuilder.stage("context", now, now, ("message",), ("MessageContext",)),
            TraceBuilder.stage(
                "personalization", now, now, ("MessageContext",), ("PersonalizationProfile",)
            ),
            TraceBuilder.stage(
                "retrieval",
                now,
                now,
                ("MessageContext", "PersonalizationProfile"),
                ("EvidenceBundle",),
            ),
            TraceBuilder.stage(
                "features",
                now,
                now,
                ("MessageContext", "PersonalizationProfile", "EvidenceBundle"),
                ("DecisionFeatures",),
            ),
            TraceBuilder.stage("signals", now, now, ("DecisionFeatures",), ("DecisionSignals",)),
        )
        trace = TraceBuilder.build(stages, str(uuid4()))
        packet = DecisionPacketFactory.build(
            context,
            personalization,
            evidence,
            features,
            signals,
            trace,
            ExecutionMetadata(
                created_at=now, duration_ms=round((perf_counter() - started) * 1000, 3)
            ),
        )
        self._logger.info("decision_packet_created", trace_id=trace.trace_id)
        return DecisionPacketValidator.validate(packet)


class DecisionOrchestrator:
    """Public immutable orchestration boundary before reasoning."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._builder = DecisionPacketBuilder(logger)

    def build(
        self,
        context: MessageContext | None,
        personalization: PersonalizationProfile | None,
        evidence: EvidenceBundle | None,
        features: DecisionFeatures | None,
        signals: DecisionSignals | None,
    ) -> DecisionPacket:
        """Assemble one Router-Agent-ready packet without making a decision."""
        inputs = (context, personalization, evidence, features, signals)
        if any(item is None for item in inputs):
            raise DecisionPacketInputError("all five deterministic inputs are required")
        return self._builder.build(context, personalization, evidence, features, signals)  # type: ignore[arg-type]
