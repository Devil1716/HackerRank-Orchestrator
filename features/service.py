"""Deterministic feature engineering over context, profile, and evidence only."""

from collections.abc import Callable
from time import perf_counter

import structlog

from app.models import (
    DecisionFeatures,
    EvidenceBundle,
    FeatureScore,
    MessageContext,
    PersonalizationProfile,
)
from features.errors import FeatureInputError, FeatureValidationError

ALGORITHM_VERSION = "phase6-v1"
Calculator = Callable[
    [MessageContext, PersonalizationProfile | None, EvidenceBundle | None], FeatureScore
]


def _score(
    name: str,
    value: float,
    confidence: float,
    inputs: tuple[str, ...],
    evidence: tuple[str, ...] = (),
) -> FeatureScore:
    return FeatureScore(
        name=name,
        value=max(0.0, min(1.0, value)),
        confidence=max(0.0, min(1.0, confidence)),
        inputs_used=inputs,
        algorithm_version=ALGORITHM_VERSION,
        supporting_evidence_ids=evidence,
    )


class FeatureFactory:
    """Build independently named deterministic feature calculators."""

    @staticmethod
    def calculators() -> dict[str, Calculator]:
        return {
            "relationship_score": lambda c, p, e: _score(
                "relationship_score",
                p.relationship.strength if p and p.relationship else 0.0,
                1.0 if p and p.relationship else 0.0,
                ("personalization.relationship",),
            ),
            "urgency_score": lambda c, p, e: _score(
                "urgency_score",
                1.0 if "urgent" in c.message.message_text.lower() else 0.0,
                1.0,
                ("message.message_text",),
            ),
            "spam_score": lambda c, p, e: _score(
                "spam_score",
                1.0 if c.message.forwarded_count >= 3 else 0.0,
                1.0,
                ("message.forwarded_count",),
            ),
            "risk_score": lambda c, p, e: _score(
                "risk_score",
                1.0 - (p.business_trust.trust if p and p.business_trust else 0.0),
                0.8,
                ("personalization.business_trust",),
            ),
            "business_trust_score": lambda c, p, e: _score(
                "business_trust_score",
                p.business_trust.trust if p and p.business_trust else 0.0,
                1.0 if p and p.business_trust else 0.0,
                ("personalization.business_trust",),
            ),
            "forward_risk": lambda c, p, e: _score(
                "forward_risk",
                min(c.message.forwarded_count / 5.0, 1.0),
                1.0,
                ("message.forwarded_count",),
            ),
            "media_importance": lambda c, p, e: _score(
                "media_importance", 0.5 if c.media else 0.0, 1.0, ("context.media",)
            ),
            "topic_continuity": lambda c, p, e: _score(
                "topic_continuity",
                min(len(p.topics) / 3.0, 1.0) if p else 0.0,
                0.8 if p else 0.0,
                ("personalization.topics",),
            ),
            "conversation_momentum": lambda c, p, e: _score(
                "conversation_momentum",
                min(len(c.conversation_history) / 10.0, 1.0),
                1.0,
                ("context.conversation_history",),
            ),
            "conversation_recency": lambda c, p, e: _score(
                "conversation_recency",
                1.0
                if c.conversation_statistics.last_message_at
                and (
                    c.message.created_at - c.conversation_statistics.last_message_at
                ).total_seconds()
                <= 86400
                else 0.0,
                0.9,
                ("context.timestamps",),
            ),
            "conversation_frequency": lambda c, p, e: _score(
                "conversation_frequency",
                min(len(c.conversation_history) / 50.0, 1.0),
                1.0,
                ("context.conversation_history",),
            ),
            "notification_fatigue": lambda c, p, e: _score(
                "notification_fatigue",
                min(
                    c.notification_statistics.notifications_dismissed
                    / max(c.notification_statistics.notifications_sent, 1),
                    1.0,
                ),
                1.0,
                ("context.notification_statistics",),
            ),
            "user_engagement": lambda c, p, e: _score(
                "user_engagement",
                p.behavior.engagement_frequency if p and p.behavior else 0.0,
                1.0 if p and p.behavior else 0.0,
                ("personalization.behavior",),
            ),
            "temporal_importance": lambda c, p, e: _score(
                "temporal_importance",
                1.0 if c.message.created_at.hour in range(8, 22) else 0.5,
                1.0,
                ("message.created_at",),
            ),
            "business_criticality": lambda c, p, e: _score(
                "business_criticality",
                1.0 if c.business and c.business.verified else 0.0,
                1.0,
                ("context.business",),
            ),
            "evidence_strength": lambda c, p, e: _score(
                "evidence_strength",
                min(len(e.items) / 5.0, 1.0) if e else 0.0,
                1.0 if e else 0.0,
                ("evidence.items",),
                tuple(item.evidence_id for item in e.items) if e else (),
            ),
            "retrieval_confidence": lambda c, p, e: _score(
                "retrieval_confidence",
                e.retrieval_confidence if e else 0.0,
                1.0 if e else 0.0,
                ("evidence.retrieval_confidence",),
            ),
            "context_completeness": lambda c, p, e: _score(
                "context_completeness",
                sum(value is not None for value in (c.sender, c.business, c.group, c.media)) / 4.0,
                1.0,
                ("context.optional_entities",),
            ),
            "behavior_consistency": lambda c, p, e: _score(
                "behavior_consistency",
                1.0
                - abs(
                    (p.behavior.open_rate if p and p.behavior else 0.0)
                    - (p.behavior.engagement_frequency if p and p.behavior else 0.0)
                ),
                0.8,
                ("personalization.behavior",),
            ),
            "preference_alignment": lambda c, p, e: _score(
                "preference_alignment",
                0.0
                if p and c.conversation.conversation_id in p.preferences.muted_conversation_ids
                else 1.0,
                1.0 if p else 0.0,
                ("personalization.preferences",),
            ),
            "media_confidence": lambda c, p, e: _score(
                "media_confidence", 1.0 if c.media else 0.0, 1.0, ("context.media",)
            ),
            "interaction_density": lambda c, p, e: _score(
                "interaction_density",
                min(len(c.interaction_history) / max(len(c.conversation_history), 1), 1.0),
                1.0,
                ("context.interaction_history",),
            ),
            "conversation_importance": lambda c, p, e: _score(
                "conversation_importance",
                1.0 if c.conversation.conversation_type.value in ("personal", "business") else 0.5,
                1.0,
                ("context.conversation",),
            ),
            "historical_similarity": lambda c, p, e: _score(
                "historical_similarity",
                sum(item.relevance for item in e.items) / len(e.items) if e and e.items else 0.0,
                1.0 if e and e.items else 0.0,
                ("evidence.items",),
            ),
            "business_interaction_strength": lambda c, p, e: _score(
                "business_interaction_strength",
                min(len(c.business_history) / 5.0, 1.0),
                1.0,
                ("context.business_history",),
            ),
        }


class FeatureValidators:
    """Validate cross-feature invariants and normalized outputs."""

    @staticmethod
    def validate(features: DecisionFeatures) -> DecisionFeatures:
        for feature in features.model_dump().values():
            if not isinstance(feature, dict) or not 0.0 <= feature["value"] <= 1.0:
                raise FeatureValidationError("feature values must be normalized")
        return features


class FeatureMetadataBuilder:
    """Build stable pipeline metadata without mutable state."""

    @staticmethod
    def build(features: DecisionFeatures) -> tuple[tuple[str, str], ...]:
        return (
            ("algorithm_version", ALGORITHM_VERSION),
            ("feature_count", str(len(features.model_fields))),
        )


class FeaturePipeline:
    """Execute validation, calculation, cross-validation, and metadata stages."""

    def __init__(
        self, calculators: dict[str, Calculator], logger: structlog.stdlib.BoundLogger
    ) -> None:
        self._calculators = calculators
        self._logger = logger

    def run(
        self,
        context: MessageContext,
        profile: PersonalizationProfile | None,
        evidence: EvidenceBundle | None,
    ) -> DecisionFeatures:
        if context is None:
            raise FeatureInputError("MessageContext is required")
        values = {}
        for name, calculator in self._calculators.items():
            started = perf_counter()
            self._logger.info("feature_started", feature=name, algorithm_version=ALGORITHM_VERSION)
            values[name] = calculator(context, profile, evidence)
            self._logger.info(
                "feature_completed",
                feature=name,
                confidence=values[name].confidence,
                duration_ms=round((perf_counter() - started) * 1000, 3),
            )
        result = FeatureValidators.validate(DecisionFeatures(**values))
        self._logger.info("feature_pipeline_completed", feature_count=len(values))
        return result


class FeatureEngineeringService:
    """Public context-only feature engineering service."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._pipeline = FeaturePipeline(FeatureFactory.calculators(), logger)

    def build(
        self,
        context: MessageContext,
        profile: PersonalizationProfile | None = None,
        evidence: EvidenceBundle | None = None,
    ) -> DecisionFeatures:
        """Build deterministic features from the three phase inputs only."""
        return self._pipeline.run(context, profile, evidence)
