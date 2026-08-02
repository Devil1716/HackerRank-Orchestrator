"""Explicit composition of configured CSV repositories."""

from dataclasses import dataclass

from app.config.settings import Settings
from repositories.base import (
    BusinessHistoryRepository,
    BusinessRepository,
    ConversationRepository,
    GroupMembershipRepository,
    GroupRepository,
    InteractionHistoryRepository,
    MediaRepository,
    MessageEventRepository,
    MessageHistoryRepository,
    MessageRepository,
    NotificationHistoryRepository,
    UserRepository,
)
from repositories.csv import (
    CsvBusinessHistoryRepository,
    CsvBusinessRepository,
    CsvConversationRepository,
    CsvGroupMembershipRepository,
    CsvGroupRepository,
    CsvInteractionHistoryRepository,
    CsvMediaRepository,
    CsvMessageEventRepository,
    CsvMessageHistoryRepository,
    CsvMessageRepository,
    CsvNotificationHistoryRepository,
    CsvUserRepository,
)


@dataclass(frozen=True)
class RepositorySet:
    """All repository ports used by the application composition root."""

    messages: MessageRepository
    users: UserRepository
    businesses: BusinessRepository
    groups: GroupRepository
    group_memberships: GroupMembershipRepository
    conversations: ConversationRepository
    media: MediaRepository
    notification_history: NotificationHistoryRepository
    interaction_history: InteractionHistoryRepository
    business_history: BusinessHistoryRepository
    message_history: MessageHistoryRepository
    message_events: MessageEventRepository


def build_repositories(settings: Settings) -> RepositorySet:
    """Build read-only CSV adapters from explicit configuration paths."""
    return RepositorySet(
        messages=CsvMessageRepository(settings.dataset_path("messages")),
        users=CsvUserRepository(settings.dataset_path("users")),
        businesses=CsvBusinessRepository(settings.dataset_path("business_accounts")),
        groups=CsvGroupRepository(settings.dataset_path("groups")),
        group_memberships=CsvGroupMembershipRepository(settings.dataset_path("group_members")),
        conversations=CsvConversationRepository(settings.dataset_path("messages")),
        media=CsvMediaRepository(
            settings.dataset_path("images"), settings.dataset_path("voice_notes")
        ),
        notification_history=CsvNotificationHistoryRepository(
            settings.dataset_path("daily_notification_summary")
        ),
        interaction_history=CsvInteractionHistoryRepository(
            settings.dataset_path("message_events")
        ),
        business_history=CsvBusinessHistoryRepository(
            settings.dataset_path("user_business_history")
        ),
        message_history=CsvMessageHistoryRepository(settings.dataset_path("message_history")),
        message_events=CsvMessageEventRepository(settings.dataset_path("message_events")),
    )
