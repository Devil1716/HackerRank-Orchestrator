"""Explicit aggregation strategies and signal construction."""

from collections.abc import Mapping

from app.models import (
    BusinessSignal,
    ContextSignal,
    DecisionSignal,
    DecisionSignals,
    EngagementSignal,
    EvidenceSignal,
    FeatureScore,
    PrioritySignal,
    RecommendationMetadata,
    RelationshipSignal,
    RiskSignal,
    SpamSignal,
    TrustSignal,
    UrgencySignal,
)

ALGORITHM_VERSION = "phase6.5-v1"


class AggregationStrategies:
    """Pure weighted-average strategies with deterministic normalization."""

    @staticmethod
    def weighted(
        features: Mapping[str, FeatureScore], weights: Mapping[str, float]
    ) -> DecisionSignal:
        available = tuple(name for name in weights if name in features)
        total = sum(weights[name] for name in available)
        if not total:
            return DecisionSignal(
                value=0.0,
                confidence=0.0,
                features_used=available,
                algorithm_version=ALGORITHM_VERSION,
                reason="No source features were available.",
            )
        value = sum(features[name].value * weights[name] for name in available) / total
        confidence = sum(features[name].confidence * weights[name] for name in available) / total
        evidence = tuple(
            evidence_id
            for name in available
            for evidence_id in features[name].supporting_evidence_ids
        )
        return DecisionSignal(
            value=value,
            confidence=confidence,
            features_used=available,
            algorithm_version=ALGORITHM_VERSION,
            supporting_evidence_ids=tuple(dict.fromkeys(evidence)),
            reason=f"Weighted aggregation of {', '.join(available)}.",
        )


class DecisionSignalFactory:
    """Create typed signals from named feature maps."""

    _weights: Mapping[str, Mapping[str, float]] = {
        "priority": {
            "urgency_score": 0.25,
            "conversation_momentum": 0.15,
            "business_criticality": 0.15,
            "relationship_score": 0.15,
            "historical_similarity": 0.15,
            "evidence_strength": 0.15,
        },
        "urgency": {"urgency_score": 0.70, "conversation_recency": 0.30},
        "risk": {
            "risk_score": 0.35,
            "forward_risk": 0.25,
            "spam_score": 0.25,
            "notification_fatigue": 0.15,
        },
        "trust": {"business_trust_score": 0.60, "relationship_score": 0.40},
        "spam": {"spam_score": 0.70, "forward_risk": 0.30},
        "relationship": {"relationship_score": 0.70, "conversation_frequency": 0.30},
        "business": {
            "business_trust_score": 0.40,
            "business_criticality": 0.30,
            "business_interaction_strength": 0.30,
        },
        "context": {"context_completeness": 0.60, "conversation_importance": 0.40},
        "engagement": {
            "user_engagement": 0.50,
            "interaction_density": 0.30,
            "conversation_momentum": 0.20,
        },
        "evidence": {
            "evidence_strength": 0.40,
            "retrieval_confidence": 0.35,
            "historical_similarity": 0.25,
        },
    }
    _types = {
        "priority": PrioritySignal,
        "urgency": UrgencySignal,
        "risk": RiskSignal,
        "trust": TrustSignal,
        "spam": SpamSignal,
        "relationship": RelationshipSignal,
        "business": BusinessSignal,
        "context": ContextSignal,
        "engagement": EngagementSignal,
        "evidence": EvidenceSignal,
    }

    def build(self, features: Mapping[str, FeatureScore]) -> DecisionSignals:
        """Build all typed signals from one feature map."""
        signals = {
            name: self._types[name](
                **AggregationStrategies.weighted(features, weights).model_dump()
            )
            for name, weights in self._weights.items()
        }
        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for signal in signals.values()
                for evidence_id in signal.supporting_evidence_ids
            )
        )
        recommendation = RecommendationMetadata(
            signals_generated=tuple(signals),
            explanation="Signals aggregate deterministic Phase 6 features; no policy decision is made.",
            source_feature_count=len(features),
            supporting_evidence_ids=evidence_ids,
        )
        return DecisionSignals(**signals, recommendation=recommendation)
