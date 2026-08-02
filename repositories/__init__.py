"""Abstract repository contracts for deterministic data access."""

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
from repositories.factory import RepositorySet, build_repositories

__all__ = [
    "BusinessRepository",
    "BusinessHistoryRepository",
    "ConversationRepository",
    "GroupRepository",
    "GroupMembershipRepository",
    "InteractionHistoryRepository",
    "MediaRepository",
    "MessageEventRepository",
    "MessageHistoryRepository",
    "MessageRepository",
    "NotificationHistoryRepository",
    "UserRepository",
    "RepositorySet",
    "build_repositories",
]
