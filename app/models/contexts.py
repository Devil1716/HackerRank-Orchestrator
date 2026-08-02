"""Immutable context aggregates passed between deterministic modules."""

from app.models.base import DomainModel
from app.models.core import (
    Business,
    BusinessHistory,
    Conversation,
    Group,
    GroupMembership,
    InteractionHistory,
    Media,
    Message,
    MessageHistory,
    NotificationHistory,
    User,
)
from app.models.value_objects import (
    BusinessID,
    ConfidenceScore,
    GroupID,
    NonNegativeCount,
    Timestamp,
    UserID,
)


class MessageContext(DomainModel):
    """Complete immutable context assembled for one incoming message."""

    message: Message
    conversation: Conversation
    recipient: User
    sender: User | None = None
    participants: tuple[User, ...] = ()
    conversation_history: tuple[MessageHistory, ...] = ()
    notification_history: tuple[NotificationHistory, ...] = ()
    interaction_history: tuple[InteractionHistory, ...] = ()
    business: Business | None = None
    business_history: tuple[BusinessHistory, ...] = ()
    group: Group | None = None
    group_memberships: tuple[GroupMembership, ...] = ()
    media: Media | None = None
    metadata: "ContextMetadata"
    timestamps: "SystemTimestamps"
    conversation_statistics: "ConversationStatistics"
    notification_statistics: "NotificationStatistics"
    business_statistics: "BusinessStatistics | None" = None
    group_statistics: "GroupStatistics | None" = None


class UserContext(DomainModel):
    """Recipient context available to personalization services."""

    user: User
    notification_count_today: NonNegativeCount = 0
    recent_open_rate: ConfidenceScore = 0.0


class BusinessContext(DomainModel):
    """Business context for messages originating from a business."""

    business: Business
    user_id: UserID
    business_id: BusinessID


class GroupContext(DomainModel):
    """Group context for messages originating in a group."""

    group: Group
    user_id: UserID
    group_id: GroupID
    is_member: bool = True


class MediaContext(DomainModel):
    """Media metadata context without OCR or speech-derived content."""

    media: Media
    extracted_text: str | None = None
    transcript: str | None = None


class NotificationContext(DomainModel):
    """Legacy aggregate retained for Phase 1 compatibility."""

    message: MessageContext
    user: UserContext
    business: BusinessContext | None = None
    group: GroupContext | None = None
    media: MediaContext | None = None


class ContextMetadata(DomainModel):
    """Non-sensitive provenance and warning metadata for a built context."""

    source: str = "repositories"
    warnings: tuple[str, ...] = ()


class SystemTimestamps(DomainModel):
    """System timestamps associated with context construction."""

    message_created_at: Timestamp
    context_built_at: Timestamp


class ConversationStatistics(DomainModel):
    """Descriptive conversation counts, not derived decision features."""

    message_count: NonNegativeCount
    participant_count: NonNegativeCount
    first_message_at: Timestamp | None = None
    last_message_at: Timestamp | None = None


class NotificationStatistics(DomainModel):
    """Descriptive notification totals for the recipient."""

    history_count: NonNegativeCount
    notifications_sent: NonNegativeCount
    notifications_dismissed: NonNegativeCount


class BusinessStatistics(DomainModel):
    """Descriptive business-account metadata."""

    messages_sent_30d: NonNegativeCount
    reports_30d: NonNegativeCount
    account_age_days: NonNegativeCount


class GroupStatistics(DomainModel):
    """Descriptive group and membership metadata."""

    member_count: NonNegativeCount
    messages_30d: NonNegativeCount
    membership_count: NonNegativeCount
