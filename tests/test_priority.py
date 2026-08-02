"""Phase 6.5 Priority and Risk Engine tests."""

import pytest
from pydantic import ValidationError

from app.services.container import build_container


def test_priority_engine_builds_compact_immutable_signals() -> None:
    """Decision features become ten explainable signals."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    evidence = container.retrieval_service.retrieve(context, profile)
    features = container.feature_engineering_service.build(context, profile, evidence)
    signals = container.priority_risk_engine.build(features)
    assert signals.priority.features_used
    assert signals.priority.reason
    assert len(signals.recommendation.signals_generated) == 10
    with pytest.raises(ValidationError):
        signals.priority = signals.priority  # type: ignore[misc]


def test_priority_engine_is_deterministic_for_cold_start() -> None:
    """The engine remains valid with the zero-valued Phase 6 output."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    features = container.feature_engineering_service.build(context)
    first = container.priority_risk_engine.build(features)
    second = container.priority_risk_engine.build(features)
    assert first == second
    assert first.evidence.value == 0
