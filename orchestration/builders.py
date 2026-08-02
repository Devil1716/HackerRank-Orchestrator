"""Decision packet builders and metadata aggregation."""

from datetime import datetime

from app.models import (
    DecisionFeatures,
    DecisionPacket,
    DecisionSignals,
    EvidenceBundle,
    ExecutionMetadata,
    FeatureMetadata,
    MessageContext,
    PersonalizationProfile,
    PipelineMetadata,
    RetrievalMetadata,
    SignalMetadata,
    TraceMetadata,
    VersionMetadata,
)
from app.models.decision_packet import TraceStage


class TraceBuilder:
    """Create immutable stage traces from explicit observations."""

    @staticmethod
    def stage(
        component: str,
        started_at: datetime,
        ended_at: datetime,
        inputs: tuple[str, ...],
        outputs: tuple[str, ...],
        warnings: tuple[str, ...] = (),
        errors: tuple[str, ...] = (),
    ) -> TraceStage:
        """Build a trace stage with a non-negative measured duration."""
        duration = max(0.0, (ended_at - started_at).total_seconds() * 1000)
        return TraceStage(
            component=component,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=round(duration, 3),
            inputs=inputs,
            outputs=outputs,
            warnings=warnings,
            errors=errors,
        )

    @staticmethod
    def build(stages: tuple[TraceStage, ...], trace_id: str) -> TraceMetadata:
        """Return the complete immutable trace."""
        return TraceMetadata(stages=stages, trace_id=trace_id)


class MetadataAggregator:
    """Copy provenance from deterministic outputs into packet sections."""

    @staticmethod
    def feature(features: DecisionFeatures) -> FeatureMetadata:
        return FeatureMetadata(
            algorithm_version=features.relationship_score.algorithm_version,
            feature_names=tuple(type(features).model_fields),
        )

    @staticmethod
    def retrieval(evidence: EvidenceBundle) -> RetrievalMetadata:
        return RetrievalMetadata(
            retrievers_used=evidence.retrievers_used,
            candidate_count=evidence.candidate_count,
            retrieval_confidence=evidence.retrieval_confidence,
        )

    @staticmethod
    def signal(signals: DecisionSignals) -> SignalMetadata:
        return SignalMetadata(
            algorithm_version=signals.recommendation.algorithm_version,
            signal_names=signals.recommendation.signals_generated,
            explanation=signals.recommendation.explanation,
        )


class DecisionPacketFactory:
    """Construct the complete packet from validated sections."""

    @staticmethod
    def build(
        context: MessageContext,
        personalization: PersonalizationProfile,
        evidence: EvidenceBundle,
        features: DecisionFeatures,
        signals: DecisionSignals,
        trace: TraceMetadata,
        execution: ExecutionMetadata,
    ) -> DecisionPacket:
        return DecisionPacket(
            context=context,
            personalization=personalization,
            evidence=evidence,
            features=features,
            signals=signals,
            feature_metadata=MetadataAggregator.feature(features),
            retrieval_metadata=MetadataAggregator.retrieval(evidence),
            signal_metadata=MetadataAggregator.signal(signals),
            pipeline_metadata=PipelineMetadata(),
            trace_metadata=trace,
            execution_metadata=execution,
            version_metadata=VersionMetadata(),
        )
