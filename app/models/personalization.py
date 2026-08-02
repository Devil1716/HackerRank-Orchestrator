"""Immutable deterministic personalization and evidence profiles."""

from datetime import datetime

from app.models.base import DomainModel
from app.models.enums import BusinessCategory, EvidenceType, RelationshipType
from app.models.value_objects import BusinessID, ConfidenceScore, Identifier, UserID


class RelationshipProfile(DomainModel):
    """User relationship to a sender or conversation."""

    user_id: UserID
    relationship_type: RelationshipType
    strength: ConfidenceScore
    source: str = "observed"
    contact_id: Identifier | None = None
    evidence_count: int = 0


class NotificationPreferences(DomainModel):
    """Explicit or observed notification preferences."""

    user_id: UserID
    do_not_disturb_window: str | None = None
    muted_conversation_ids: tuple[Identifier, ...] = ()
    digest_enabled: bool = True
    preferred_conversation_types: tuple[str, ...] = ()
    muted_business_ids: tuple[BusinessID, ...] = ()


class BehaviorProfile(DomainModel):
    """Aggregated user behavior measurements."""

    user_id: UserID
    open_rate: ConfidenceScore
    reply_rate: ConfidenceScore
    dismissal_rate: ConfidenceScore
    report_rate: ConfidenceScore
    average_response_delay_minutes: float | None = None
    conversation_initiation_rate: ConfidenceScore = 0.0
    engagement_frequency: ConfidenceScore = 0.0
    active_hours: tuple[int, ...] = ()
    communication_intensity: ConfidenceScore = 0.0


class BusinessTrustProfile(DomainModel):
    """User-specific trust relationship with a business."""

    user_id: UserID
    business_id: BusinessID
    category: BusinessCategory
    trust: ConfidenceScore
    has_recent_transaction: bool = False
    interaction_frequency: int = 0
    recurring: bool = False


class TopicProfile(DomainModel):
    """User affinity for a topic represented by an opaque topic ID."""

    user_id: UserID
    topic_id: Identifier
    affinity: ConfidenceScore
    occurrence_count: int = 0
    last_occurrence_at: datetime | None = None
    recurring: bool = False


class InteractionProfile(DomainModel):
    """Descriptive interaction totals derived from the supplied context."""

    user_id: UserID
    conversation_message_count: int = 0
    interaction_count: int = 0
    opened_count: int = 0
    replied_count: int = 0
    dismissed_count: int = 0
    reported_count: int = 0
    business_interaction_count: int = 0
    last_interaction_at: datetime | None = None


class EvidenceDescriptor(DomainModel):
    """Metadata describing profile evidence; it is not retrieved content."""

    evidence_type: EvidenceType
    reference_ids: tuple[Identifier, ...] = ()
    summary: str
    confidence: ConfidenceScore = 1.0
    time_start: datetime | None = None
    time_end: datetime | None = None
    media_ids: tuple[Identifier, ...] = ()


class EvidenceProfile(DomainModel):
    """Immutable evidence descriptors prepared for later consumers."""

    descriptors: tuple[EvidenceDescriptor, ...] = ()


class PersonalizationProfile(DomainModel):
    """Complete user-specific profile from independent signals."""

    user_id: UserID
    relationship: RelationshipProfile | None = None
    preferences: NotificationPreferences
    behavior: BehaviorProfile | None = None
    business_trust: BusinessTrustProfile | None = None
    topics: tuple[TopicProfile, ...] = ()
    interaction: InteractionProfile | None = None
    business_trust_profiles: tuple[BusinessTrustProfile, ...] = ()
    evidence: EvidenceProfile = EvidenceProfile()
