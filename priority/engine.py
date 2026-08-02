"""Priority and Risk Engine orchestration."""

from time import perf_counter

import structlog

from app.models import DecisionFeatures, DecisionSignals, RecommendationMetadata
from priority.strategies import DecisionSignalFactory
from priority.validators import SignalValidators


class SignalBuilder:
    """Convert the immutable DecisionFeatures model into one-pass mappings."""

    @staticmethod
    def build(features: DecisionFeatures) -> dict[str, object]:
        """Return feature scores without accessing any external dependency."""
        return {
            name: getattr(features, name)
            for name in type(features).model_fields
            if name != "metadata"
        }


class SignalMetadataBuilder:
    """Build stable recommendation metadata from generated signals."""

    @staticmethod
    def build(signals: DecisionSignals, feature_count: int) -> RecommendationMetadata:
        """Return structured provenance without introducing policy."""
        evidence = tuple(
            dict.fromkeys(
                evidence_id
                for name, signal in signals
                if name != "recommendation"
                for evidence_id in signal.supporting_evidence_ids
            )
        )
        return RecommendationMetadata(
            signals_generated=tuple(
                name for name in type(signals).model_fields if name != "recommendation"
            ),
            explanation="Signals aggregate deterministic Phase 6 features; no policy decision is made.",
            source_feature_count=feature_count,
            supporting_evidence_ids=evidence,
        )


class PriorityRiskEngine:
    """Build compact explainable signals from DecisionFeatures only."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._factory = DecisionSignalFactory()
        self._logger = logger

    def build(self, features: DecisionFeatures) -> DecisionSignals:
        """Aggregate, validate, and return immutable decision signals."""
        started = perf_counter()
        self._logger.info("signal_generation_started", algorithm_version="phase6.5-v1")
        mapped = SignalBuilder.build(features)
        signals = self._factory.build(mapped)  # type: ignore[arg-type]
        signals = signals.model_copy(
            update={
                "recommendation": SignalMetadataBuilder.build(signals, len(mapped)),
            }
        )
        self._logger.info("signals_aggregated", signal_count=10)
        validated = SignalValidators.validate(signals)
        self._logger.info(
            "signals_validated",
            signal_count=10,
            duration_ms=round((perf_counter() - started) * 1000, 3),
        )
        return validated
