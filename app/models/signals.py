"""Immutable compact signals derived from deterministic decision features."""

from app.models.base import DomainModel
from app.models.value_objects import ConfidenceScore


class DecisionSignal(DomainModel):
    """One explainable aggregated signal."""

    value: ConfidenceScore
    confidence: ConfidenceScore
    features_used: tuple[str, ...] = ()
    algorithm_version: str = "phase6.5-v1"
    supporting_evidence_ids: tuple[str, ...] = ()
    reason: str


class PrioritySignal(DecisionSignal):
    """Aggregate priority signal for later routing."""


class UrgencySignal(DecisionSignal):
    """Aggregate urgency signal."""


class RiskSignal(DecisionSignal):
    """Aggregate risk signal."""


class TrustSignal(DecisionSignal):
    """Aggregate trust signal."""


class SpamSignal(DecisionSignal):
    """Aggregate spam signal."""


class RelationshipSignal(DecisionSignal):
    """Aggregate relationship signal."""


class BusinessSignal(DecisionSignal):
    """Aggregate business signal."""


class ContextSignal(DecisionSignal):
    """Aggregate context completeness signal."""


class EngagementSignal(DecisionSignal):
    """Aggregate engagement signal."""


class EvidenceSignal(DecisionSignal):
    """Aggregate evidence signal."""


class RecommendationMetadata(DomainModel):
    """Structured provenance and explainability metadata."""

    algorithm_version: str = "phase6.5-v1"
    signals_generated: tuple[str, ...] = ()
    explanation: str
    source_feature_count: int = 0
    supporting_evidence_ids: tuple[str, ...] = ()


class DecisionSignals(DomainModel):
    """Compact immutable signal set passed to a future Router Agent."""

    priority: PrioritySignal
    urgency: UrgencySignal
    risk: RiskSignal
    trust: TrustSignal
    spam: SpamSignal
    relationship: RelationshipSignal
    business: BusinessSignal
    context: ContextSignal
    engagement: EngagementSignal
    evidence: EvidenceSignal
    recommendation: RecommendationMetadata
