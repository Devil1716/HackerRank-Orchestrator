"""Deterministic context orchestration over repository interfaces."""

from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from typing import TypeVar

import structlog

from app.config.settings import Settings
from app.models import (
    Business,
    BusinessHistory,
    BusinessStatistics,
    ContextMetadata,
    Conversation,
    ConversationStatistics,
    Group,
    GroupMembership,
    GroupStatistics,
    InteractionHistory,
    Media,
    Message,
    MessageContext,
    MessageHistory,
    NotificationHistory,
    NotificationStatistics,
    SystemTimestamps,
    User,
)
from context.errors import (
    ContextBuilderError,
    ContextConstructionError,
    ConversationNotFoundError,
    MessageNotFoundError,
    RecipientNotFoundError,
    RepositoryQueryError,
)
from context.ports import ContextBuilder
from repositories.factory import RepositorySet
from utils.errors import RepositoryError
from utils.time import utc_now

ResultT = TypeVar("ResultT")


class ContextBuilderService(ContextBuilder):
    """Assemble context without interpreting or scoring its contents."""

    def __init__(
        self,
        repositories: RepositorySet,
        settings: Settings,
        logger: structlog.stdlib.BoundLogger,
    ) -> None:
        """Create a builder from explicit repository, settings, and logging dependencies."""
        self.repositories = repositories
        self.settings = settings
        self.logger = logger

    def build(self, message: Message | str) -> MessageContext:
        """Build a complete context and wrap repository failures safely."""
        try:
            message_model = self._load_message(message)
        except RepositoryError as exc:
            self.logger.error(
                "context_build_failed",
                message_id=str(message),
                error_type=type(exc).__name__,
            )
            raise RepositoryQueryError("repository query failed while loading message") from exc
        message_id = message_model.message_id
        self.logger.info("context_creation_started", message_id=message_id)
        try:
            with structlog.contextvars.bound_contextvars(message_id=message_id):
                with self._stage(message_id):
                    context = self._assemble(message_model)
        except ContextBuilderError:
            self.logger.error("context_build_failed", message_id=message_id)
            raise
        except RepositoryError as exc:
            self.logger.error(
                "context_build_failed",
                message_id=message_id,
                error_type=type(exc).__name__,
            )
            raise RepositoryQueryError(f"repository query failed for {message_id}") from exc
        except Exception as exc:
            self.logger.error(
                "context_build_failed",
                message_id=message_id,
                error_type=type(exc).__name__,
            )
            raise ContextConstructionError(f"context construction failed for {message_id}") from exc
        self.logger.info("context_successfully_built", message_id=message_id)
        return context

    def _stage(self, message_id: str) -> AbstractContextManager[None]:
        """Return the existing structured stage lifecycle context manager."""
        from app.monitoring.logging import stage_log

        return stage_log(self.logger, message_id=message_id, stage="context_builder")

    def _load_message(self, message: Message | str) -> Message:
        """Resolve an ID through the message repository or accept a typed message."""
        if isinstance(message, Message):
            return message
        resolved = self._query("messages", self.repositories.messages.get, message)
        if resolved is None:
            raise MessageNotFoundError(f"message not found: {message}")
        return resolved

    def _assemble(self, message: Message) -> MessageContext:
        """Execute the fixed orchestration sequence."""
        recipient = self._required_user(message.user_id)
        conversation = self._required_conversation(message.conversation_id)
        sender = self._optional_user(message.sender_user_id, message.message_id, "sender")
        business = self._optional_business(message.business_id, message.message_id)
        group = self._optional_group(message.group_id, message.message_id)
        group_memberships = self._group_memberships(message.group_id, message.message_id)
        participants = self._participants(conversation, group_memberships, message.message_id)
        conversation_history = self._history(message)
        notification_history = self._notification_history(message)
        interaction_history = self._interaction_history(message)
        business_history = self._business_history(message)
        media = self._media(message)
        return MessageContext(
            message=message,
            conversation=conversation,
            recipient=recipient,
            sender=sender,
            participants=participants,
            conversation_history=conversation_history,
            notification_history=notification_history,
            interaction_history=interaction_history,
            business=business,
            business_history=business_history,
            group=group,
            group_memberships=group_memberships,
            media=media,
            metadata=ContextMetadata(warnings=()),
            timestamps=SystemTimestamps(
                message_created_at=message.created_at,
                context_built_at=utc_now(),
            ),
            conversation_statistics=self._conversation_statistics(
                message, conversation_history, participants
            ),
            notification_statistics=self._notification_statistics(notification_history),
            business_statistics=self._business_statistics(business),
            group_statistics=self._group_statistics(group, group_memberships),
        )

    def _required_user(self, user_id: str) -> User:
        """Resolve the required recipient or raise a context-specific error."""
        user = self._query("users", self.repositories.users.get, user_id)
        if user is None:
            raise RecipientNotFoundError(f"recipient not found: {user_id}")
        return user

    def _required_conversation(self, conversation_id: str) -> Conversation:
        """Resolve the required normalized conversation."""
        conversation = self._query(
            "conversations", self.repositories.conversations.get, conversation_id
        )
        if conversation is None:
            raise ConversationNotFoundError(f"conversation not found: {conversation_id}")
        return conversation

    def _optional_user(self, user_id: str | None, message_id: str, role: str) -> User | None:
        """Resolve an optional participant and log only non-sensitive identifiers."""
        if user_id is None:
            return None
        user = self._query("users", self.repositories.users.get, user_id)
        if user is None:
            self._missing(message_id, role, user_id)
        return user

    def _optional_business(self, business_id: str | None, message_id: str) -> Business | None:
        """Resolve optional business metadata."""
        if business_id is None:
            return None
        business = self._query("businesses", self.repositories.businesses.get, business_id)
        if business is None:
            self._missing(message_id, "business", business_id)
        return business

    def _optional_group(self, group_id: str | None, message_id: str) -> Group | None:
        """Resolve optional group metadata."""
        if group_id is None:
            return None
        group = self._query("groups", self.repositories.groups.get, group_id)
        if group is None:
            self._missing(message_id, "group", group_id)
        return group

    def _group_memberships(
        self, group_id: str | None, message_id: str
    ) -> tuple[GroupMembership, ...]:
        """Resolve group membership metadata when the message belongs to a group."""
        if group_id is None:
            return ()
        return self._query(
            "group_memberships", self.repositories.group_memberships.for_group, group_id
        )

    def _participants(
        self,
        conversation: Conversation,
        memberships: Iterable[GroupMembership],
        message_id: str,
    ) -> tuple[User, ...]:
        """Resolve known participant IDs, logging missing optional users."""
        membership_ids = tuple(membership.user_id for membership in memberships)
        participant_ids = tuple(dict.fromkeys(conversation.participant_user_ids + membership_ids))
        users = self._query("participants", self.repositories.users.get_many, participant_ids)
        found = {user.user_id for user in users}
        for participant_id in participant_ids:
            if participant_id not in found:
                self._missing(message_id, "participant", participant_id)
        return users

    def _history(self, message: Message) -> tuple[MessageHistory, ...]:
        """Load bounded conversation history through the history repository."""
        return self._query(
            "conversation_history",
            self.repositories.message_history.find_for_message,
            message,
            limit=self.settings.context_history_limit,
        )

    def _notification_history(self, message: Message) -> tuple[NotificationHistory, ...]:
        """Load recipient notification history."""
        return self._query(
            "notification_history", self.repositories.notification_history.for_user, message.user_id
        )

    def _interaction_history(self, message: Message) -> tuple[InteractionHistory, ...]:
        """Load interactions for the incoming message."""
        return self._query(
            "interaction_history",
            self.repositories.interaction_history.for_message,
            message.message_id,
        )

    def _business_history(self, message: Message) -> tuple[BusinessHistory, ...]:
        """Load only the recipient's relationship records for this business."""
        if message.business_id is None:
            return ()
        history = self._query(
            "business_history", self.repositories.business_history.for_user, message.user_id
        )
        return tuple(item for item in history if item.business_id == message.business_id)

    def _media(self, message: Message) -> Media | None:
        """Resolve optional media metadata without inspecting media content."""
        if message.media_id is None:
            return None
        media = self._query("media", self.repositories.media.get, message.media_id)
        if media is None:
            self._missing(message.message_id, "media", message.media_id)
        return media

    @staticmethod
    def _conversation_statistics(
        message: Message, history: tuple[MessageHistory, ...], participants: tuple[User, ...]
    ) -> ConversationStatistics:
        """Compute descriptive conversation metadata only."""
        timestamps = tuple(item.created_at for item in history) + (message.created_at,)
        return ConversationStatistics(
            message_count=len(timestamps),
            participant_count=len(participants),
            first_message_at=min(timestamps),
            last_message_at=max(timestamps),
        )

    @staticmethod
    def _notification_statistics(
        history: tuple[NotificationHistory, ...],
    ) -> NotificationStatistics:
        """Compute descriptive notification totals."""
        return NotificationStatistics(
            history_count=len(history),
            notifications_sent=sum(item.notifications_sent for item in history),
            notifications_dismissed=sum(item.notifications_dismissed for item in history),
        )

    @staticmethod
    def _business_statistics(business: Business | None) -> BusinessStatistics | None:
        """Project business metadata into a descriptive statistics model."""
        if business is None:
            return None
        return BusinessStatistics(
            messages_sent_30d=business.messages_sent_30d,
            reports_30d=business.reports_30d,
            account_age_days=business.account_age_days,
        )

    @staticmethod
    def _group_statistics(
        group: Group | None, memberships: tuple[GroupMembership, ...]
    ) -> GroupStatistics | None:
        """Project group metadata into a descriptive statistics model."""
        if group is None:
            return None
        return GroupStatistics(
            member_count=group.member_count,
            messages_30d=group.messages_30d,
            membership_count=len(memberships),
        )

    def _query(
        self,
        repository_name: str,
        operation: Callable[..., ResultT],
        *args: object,
        **kwargs: object,
    ) -> ResultT:
        """Log repository operations without logging message contents."""
        self.logger.info("repository_queried", repository=repository_name)
        return operation(*args, **kwargs)

    def _missing(self, message_id: str, resource: str, resource_id: str) -> None:
        """Log missing optional data without sensitive payloads."""
        self.logger.warning(
            "context_optional_data_missing",
            message_id=message_id,
            resource=resource,
            resource_id=resource_id,
        )
