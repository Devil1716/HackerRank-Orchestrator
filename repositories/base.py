"""Abstract repository contracts independent of storage technology."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from app.models import (
    Business,
    BusinessHistory,
    Conversation,
    Group,
    GroupMembership,
    InteractionHistory,
    Media,
    Message,
    MessageEvent,
    MessageHistory,
    NotificationHistory,
    User,
)


class Repository[EntityT](ABC):
    """Common read-only repository operations."""

    @abstractmethod
    def get(self, record_id: str) -> EntityT | None:
        """Return one record by primary key."""
        raise NotImplementedError

    @abstractmethod
    def get_many(self, record_ids: Sequence[str]) -> tuple[EntityT, ...]:
        """Return records in caller-provided ID order, omitting misses."""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> tuple[EntityT, ...]:
        """Return all records as an immutable tuple."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, record_id: str) -> bool:
        """Return whether a primary key exists."""
        raise NotImplementedError


class MessageRepository(Repository[Message], ABC):
    """Access incoming messages."""

    def list_messages(self) -> tuple[Message, ...]:
        """Backward-compatible alias for ``list``."""
        return self.list()

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[Message, ...]:
        """Return messages addressed to a user."""
        raise NotImplementedError

    @abstractmethod
    def for_conversation(self, conversation_id: str) -> tuple[Message, ...]:
        """Return messages belonging to a normalized conversation."""
        raise NotImplementedError

    @abstractmethod
    def between(self, start: datetime, end: datetime) -> tuple[Message, ...]:
        """Return messages in the inclusive time range."""
        raise NotImplementedError


class UserRepository(Repository[User], ABC):
    """Access notification-recipient profiles."""


class BusinessRepository(Repository[Business], ABC):
    """Access business-account metadata."""


class GroupRepository(Repository[Group], ABC):
    """Access group metadata."""


class GroupMembershipRepository(Repository[GroupMembership], ABC):
    """Access user membership records for groups."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[GroupMembership, ...]:
        """Return group memberships for a user."""
        raise NotImplementedError

    @abstractmethod
    def for_group(self, group_id: str) -> tuple[GroupMembership, ...]:
        """Return members for a group."""
        raise NotImplementedError


class ConversationRepository(Repository[Conversation], ABC):
    """Access normalized conversation envelopes."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[Conversation, ...]:
        """Return conversations associated with a user."""
        raise NotImplementedError


class MediaRepository(Repository[Media], ABC):
    """Access image and voice-note media references."""


class NotificationHistoryRepository(Repository[NotificationHistory], ABC):
    """Access daily notification summaries and notification history."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[NotificationHistory, ...]:
        """Return notification history for a user."""
        raise NotImplementedError

    @abstractmethod
    def between(self, start: datetime, end: datetime) -> tuple[NotificationHistory, ...]:
        """Return notification history in the inclusive time range."""
        raise NotImplementedError


class InteractionHistoryRepository(Repository[InteractionHistory], ABC):
    """Access historical user-message interactions."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[InteractionHistory, ...]:
        """Return interactions for a user."""
        raise NotImplementedError

    @abstractmethod
    def for_message(self, message_id: str) -> tuple[InteractionHistory, ...]:
        """Return interactions for a message."""
        raise NotImplementedError

    @abstractmethod
    def between(self, start: datetime, end: datetime) -> tuple[InteractionHistory, ...]:
        """Return timestamped interactions in the inclusive time range."""
        raise NotImplementedError


class BusinessHistoryRepository(Repository[BusinessHistory], ABC):
    """Access user-business relationship history."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[BusinessHistory, ...]:
        """Return business relationships for a user."""
        raise NotImplementedError

    @abstractmethod
    def for_business(self, business_id: str) -> tuple[BusinessHistory, ...]:
        """Return user relationships for a business."""
        raise NotImplementedError


class MessageHistoryRepository(Repository[MessageHistory], ABC):
    """Backward-compatible historical-message repository contract."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[MessageHistory, ...]:
        """Return historical messages for a user."""
        raise NotImplementedError

    @abstractmethod
    def between(self, start: datetime, end: datetime) -> tuple[MessageHistory, ...]:
        """Return historical messages in the inclusive time range."""
        raise NotImplementedError

    @abstractmethod
    def find_for_message(self, message: Message, *, limit: int) -> tuple[MessageHistory, ...]:
        """Return bounded history for the same user as an incoming message."""
        raise NotImplementedError


class MessageEventRepository(Repository[MessageEvent], ABC):
    """Backward-compatible raw message-event repository contract."""

    @abstractmethod
    def for_user(self, user_id: str) -> tuple[MessageEvent, ...]:
        """Return events for a user."""
        raise NotImplementedError

    @abstractmethod
    def for_message(self, message_id: str) -> tuple[MessageEvent, ...]:
        """Return events for a message."""
        raise NotImplementedError
