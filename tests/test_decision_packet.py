"""Phase 6.75 Decision Packet tests."""

import pytest
from pydantic import ValidationError

from app.services.container import build_container
from orchestration.errors import DecisionPacketInputError


def _build_packet() -> object:
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    evidence = container.retrieval_service.retrieve(context, profile)
    features = container.feature_engineering_service.build(context, profile, evidence)
    signals = container.priority_risk_engine.build(features)
    return container.decision_orchestrator.build(context, profile, evidence, features, signals)


def test_packet_contains_all_sections_and_trace() -> None:
    """Orchestration produces a complete immutable packet."""
    packet = _build_packet()
    assert packet.trace_metadata.stages
    assert packet.feature_metadata.feature_names
    assert packet.signal_metadata.signal_names
    assert packet.execution_metadata.duration_ms >= 0
    with pytest.raises(ValidationError):
        packet.signals = packet.signals  # type: ignore[misc]


def test_packet_requires_all_top_level_inputs() -> None:
    """Missing deterministic sections fail before packet construction."""
    container = build_container()
    with pytest.raises(DecisionPacketInputError):
        container.decision_orchestrator.build(None, None, None, None, None)
