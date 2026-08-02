"""Phase 6 deterministic feature-engineering tests."""

import pytest
from pydantic import ValidationError

from app.services.container import build_container


def test_feature_pipeline_builds_complete_immutable_vector() -> None:
    """All requested feature families are present and frozen."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    evidence = container.retrieval_service.retrieve(context, profile)
    features = container.feature_engineering_service.build(context, profile, evidence)
    assert len(type(features).model_fields) == 25
    assert features.retrieval_confidence.algorithm_version == "phase6-v1"
    with pytest.raises(ValidationError):
        features.urgency_score = features.urgency_score  # type: ignore[misc]


def test_feature_pipeline_is_deterministic_for_cold_start_inputs() -> None:
    """Missing optional profile and evidence inputs remain valid and repeatable."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    first = container.feature_engineering_service.build(context)
    second = container.feature_engineering_service.build(context)
    assert first == second
    assert first.retrieval_confidence.value == 0
    assert first.evidence_strength.value == 0
