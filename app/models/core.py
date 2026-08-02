"""Core entities and histories in the Cortex Notify domain."""

from pydantic import Field

from app.models.base import DomainModel
from app.models.enums import (
    ActionType,
    BusinessCategory,
    ConversationType,
    InteractionType,
    MediaType,
    RelationshipType,
)
from app.models.value_objects import (
    BusinessID,
    ConversationID,
    GroupID,
    Identifier,
    MessageID,
    NonNegativeCount,
    Timestamp,
    UserID,
)


class Message(DomainModel):
    """An incoming WhatsApp message before interpretation."""

    message_id: MessageID
    user_id: UserID
    conversation_id: ConversationID
    conversation_type: ConversationType
    created_at: Timestamp
    message_text: str = ""
    sender_user_id: UserID | None = None
    business_id: BusinessID | None = None
    group_id: GroupID | None = None
    media_id: Identifier | None = None
    media_type: MediaType | None = None
    forwarded_count: NonNegativeCount = 0


class MessageHistory(Message):
    """Historical message with the same normalized shape as an incoming message."""


class User(DomainModel):
    """A notification recipient and stable account metadata."""

    user_id: UserID
    display_name: str | None = Field(default=None, max_length=200)
    timezone: str = "UTC"
    locale: str = "en"
    do_not_disturb_window: str | None = None
    messages_opened_30d: NonNegativeCount = 0
    messages_replied_30d: NonNegativeCount = 0
    notifications_dismissed_30d: NonNegativeCount = 0
    messages_reported_30d: NonNegativeCount = 0


class Business(DomainModel):
    """Metadata describing a business sender."""

    business_id: BusinessID
    display_name: str = Field(min_length=1, max_length=200)
    category: BusinessCategory = BusinessCategory.UNKNOWN
    verified: bool = False
    domain: str | None = None
    account_age_days: NonNegativeCount = 0
    reports_30d: NonNegativeCount = 0
    brand_name: str | None = None
    official_domain: str | None = None
    domain_used_by_sender: str | None = None
    messages_sent_30d: NonNegativeCount = 0
    domain_used_by_sender_age_days: NonNegativeCount = 0


class Group(DomainModel):
    """Metadata describing a group conversation."""

    group_id: GroupID
    display_name: str = Field(min_length=1, max_length=200)
    group_type: str = "general"
    member_count: NonNegativeCount = 0
    admin_user_ids: tuple[UserID, ...] = ()
    admin_count: NonNegativeCount = 0
    messages_30d: NonNegativeCount = 0
    created_at: Timestamp | None = None


class GroupMembership(DomainModel):
    """A user's membership and observed activity within a group."""

    membership_id: Identifier
    group_id: GroupID
    user_id: UserID
    role: str
    joined_at: Timestamp
    messages_sent_30d: NonNegativeCount = 0
    messages_read_30d: NonNegativeCount = 0
    replies_sent_30d: NonNegativeCount = 0
    notifications_dismissed_30d: NonNegativeCount = 0
    group_muted_by_user: bool = False


class Media(DomainModel):
    """A media reference; content extraction belongs to later adapters."""

    media_id: Identifier
    media_type: MediaType
    file_path: str = Field(min_length=1)
    mime_type: str | None = None
    byte_size: NonNegativeCount | None = None


class Conversation(DomainModel):
    """A conversation envelope linking a message to participants."""

    conversation_id: ConversationID
    conversation_type: ConversationType
    user_id: UserID
    group_id: GroupID | None = None
    business_id: BusinessID | None = None
    participant_user_ids: tuple[UserID, ...] = ()


class NotificationHistory(DomainModel):
    """A previously delivered notification outcome."""

    history_id: Identifier
    user_id: UserID
    message_id: MessageID | None = None
    action: ActionType | None = None
    created_at: Timestamp | None = None
    opened: bool = False
    dismissed: bool = False
    notifications_sent: NonNegativeCount = 0
    notifications_dismissed: NonNegativeCount = 0


class InteractionHistory(DomainModel):
    """A recorded user interaction with a historical message."""

    interaction_id: Identifier
    user_id: UserID
    message_id: MessageID
    interaction_type: InteractionType | None = None
    created_at: Timestamp | None = None
    message_opened: bool = False
    message_replied: bool = False
    reaction_time_minutes: NonNegativeCount | None = None
    notification_dismissed: bool = False
    muted_after_message: bool = False
    message_reported: bool = False


class MessageEvent(DomainModel):
    """Raw interaction event normalized from the message-events dataset."""

    user_id: UserID
    message_id: MessageID
    message_opened: bool = False
    message_replied: bool = False
    reaction_time_minutes: NonNegativeCount | None = None
    notification_dismissed: bool = False
    muted_after_message: bool = False
    message_reported: bool = False


class BusinessHistory(DomainModel):
    """A user's historical relationship with a business account."""

    history_id: Identifier
    user_id: UserID
    business_id: BusinessID
    relationship: RelationshipType = RelationshipType.UNKNOWN
    order_count: NonNegativeCount = 0
    opted_in: bool = False
    opted_out: bool = False
    last_interaction_at: Timestamp | None = None
    why_user_knows_account: str | None = None
    activity_count_180d: NonNegativeCount = 0
    messages_opened_30d: NonNegativeCount = 0
    messages_dismissed_30d: NonNegativeCount = 0
    messages_replied_30d: NonNegativeCount = 0
    last_reply_at: Timestamp | None = None
