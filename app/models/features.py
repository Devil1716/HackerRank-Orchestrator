"""Feature score value objects with no feature-generation implementation."""

from app.models.base import DomainModel
from app.models.value_objects import ConfidenceScore


class FeatureScore(DomainModel):
    """A normalized score and its confidence."""

    value: ConfidenceScore
    confidence: ConfidenceScore
    name: str = "feature"
    inputs_used: tuple[str, ...] = ()
    algorithm_version: str = "1.0"
    supporting_evidence_ids: tuple[str, ...] = ()


class RelationshipScore(FeatureScore):
    """Normalized relationship strength."""


class UrgencyScore(FeatureScore):
    """Normalized urgency signal."""


class RiskScore(FeatureScore):
    """Normalized safety or trust risk signal."""


class SpamScore(FeatureScore):
    """Normalized spam likelihood signal."""


class BusinessTrustScore(FeatureScore):
    """Normalized business trust signal."""


class NotificationFatigueScore(FeatureScore):
    """Normalized notification fatigue signal."""


class TopicContinuityScore(FeatureScore):
    """Normalized topic continuity signal."""


class MediaImportanceScore(FeatureScore):
    """Normalized media importance signal."""


class UserEngagementScore(FeatureScore):
    """Normalized user engagement signal."""


class DecisionFeatures(DomainModel):
    """Complete immutable deterministic feature vector for later routing."""

    relationship_score: FeatureScore
    urgency_score: FeatureScore
    spam_score: FeatureScore
    risk_score: FeatureScore
    business_trust_score: FeatureScore
    forward_risk: FeatureScore
    media_importance: FeatureScore
    topic_continuity: FeatureScore
    conversation_momentum: FeatureScore
    conversation_recency: FeatureScore
    conversation_frequency: FeatureScore
    notification_fatigue: FeatureScore
    user_engagement: FeatureScore
    temporal_importance: FeatureScore
    business_criticality: FeatureScore
    evidence_strength: FeatureScore
    retrieval_confidence: FeatureScore
    context_completeness: FeatureScore
    behavior_consistency: FeatureScore
    preference_alignment: FeatureScore
    media_confidence: FeatureScore
    interaction_density: FeatureScore
    conversation_importance: FeatureScore
    historical_similarity: FeatureScore
    business_interaction_strength: FeatureScore


class FeatureScores(DomainModel):
    """Named feature scores passed to a future reasoning boundary."""

    relationship: RelationshipScore
    urgency: UrgencyScore
    risk: RiskScore
    spam: SpamScore
    business_trust: BusinessTrustScore
    notification_fatigue: NotificationFatigueScore
    topic_continuity: TopicContinuityScore
    media_importance: MediaImportanceScore
    user_engagement: UserEngagementScore
