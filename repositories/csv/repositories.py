"""Concrete Polars CSV repositories with typed domain-model boundaries."""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from app.models import (
    Business,
    BusinessCategory,
    BusinessHistory,
    Conversation,
    ConversationType,
    Group,
    GroupMembership,
    InteractionHistory,
    Media,
    MediaType,
    Message,
    MessageEvent,
    MessageHistory,
    NotificationHistory,
    User,
)
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
from repositories.csv.base import CsvRepository, CsvTable
from repositories.csv.parsing import (
    boolean,
    enum_value,
    integer,
    optional_enum,
    required_text,
    text,
    timestamp,
)
from utils.repository_errors import DuplicateRecordError


def _conversation_id(row: dict[str, object], path: Path, row_number: int) -> str:
    """Create the stable storage identity absent from the source CSV."""
    kind = required_text(row, "conversation_type", path, row_number)
    user_id = required_text(row, "user_id", path, row_number)
    if kind == ConversationType.GROUP.value:
        return f"group:{required_text(row, 'group_id', path, row_number)}"
    if kind == ConversationType.BUSINESS.value:
        return f"business:{user_id}:{required_text(row, 'business_id', path, row_number)}"
    sender = text(row, "sender_user_id", path, row_number) or "unknown"
    return f"personal:{user_id}:{sender}"


def _conversation_type(row: dict[str, object], path: Path, row_number: int) -> ConversationType:
    return enum_value(row, "conversation_type", ConversationType, path, row_number)


def _message_values(row: dict[str, object], path: Path, row_number: int) -> dict[str, object]:
    """Normalize shared message columns for current and historical messages."""
    return {
        "message_id": required_text(row, "message_id", path, row_number),
        "user_id": required_text(row, "user_id", path, row_number),
        "conversation_id": _conversation_id(row, path, row_number),
        "conversation_type": _conversation_type(row, path, row_number),
        "created_at": timestamp(row, "created_at", path, row_number),
        "message_text": text(row, "message_text", path, row_number) or "",
        "sender_user_id": text(row, "sender_user_id", path, row_number),
        "business_id": text(row, "business_id", path, row_number),
        "group_id": text(row, "group_id", path, row_number),
        "media_id": text(row, "media_id", path, row_number),
        "media_type": optional_enum(row, "media_type", MediaType, path, row_number),
        "forwarded_count": integer(row, "forwarded_count", path, row_number),
    }


class CsvMessageRepository(CsvRepository[Message], MessageRepository):
    """Repository for `messages.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "message_id",
                    "user_id",
                    "conversation_type",
                    "created_at",
                    "message_text",
                    "forwarded_count",
                ),
            ),
            lambda item: item.message_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> Message:
        return Message.model_validate(_message_values(row, self.table.path, row_number))

    def for_user(self, user_id: str) -> tuple[Message, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)

    def for_conversation(self, conversation_id: str) -> tuple[Message, ...]:
        return tuple(item for item in self.list() if item.conversation_id == conversation_id)

    def between(self, start: datetime, end: datetime) -> tuple[Message, ...]:
        return tuple(item for item in self.list() if start <= item.created_at <= end)


class CsvMessageHistoryRepository(CsvRepository[MessageHistory], MessageHistoryRepository):
    """Repository for `message_history.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "message_id",
                    "user_id",
                    "conversation_type",
                    "created_at",
                    "message_text",
                    "forwarded_count",
                ),
            ),
            lambda item: item.message_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> MessageHistory:
        return MessageHistory.model_validate(_message_values(row, self.table.path, row_number))

    def for_user(self, user_id: str) -> tuple[MessageHistory, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)

    def between(self, start: datetime, end: datetime) -> tuple[MessageHistory, ...]:
        return tuple(item for item in self.list() if start <= item.created_at <= end)

    def find_for_message(self, message: Message, *, limit: int) -> tuple[MessageHistory, ...]:
        """Return the most recent bounded history for the message recipient."""
        if limit < 1:
            return ()
        records = self.for_user(message.user_id)
        return tuple(sorted(records, key=lambda item: item.created_at, reverse=True)[:limit])


class CsvUserRepository(CsvRepository[User], UserRepository):
    """Repository for `users.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "user_id",
                    "do_not_disturb_window",
                    "messages_opened_30d",
                    "messages_replied_30d",
                    "notifications_dismissed_30d",
                    "messages_reported_30d",
                ),
            ),
            lambda item: item.user_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> User:
        path = self.table.path
        return User(
            user_id=required_text(row, "user_id", path, row_number),
            do_not_disturb_window=text(row, "do_not_disturb_window", path, row_number),
            messages_opened_30d=integer(row, "messages_opened_30d", path, row_number),
            messages_replied_30d=integer(row, "messages_replied_30d", path, row_number),
            notifications_dismissed_30d=integer(
                row, "notifications_dismissed_30d", path, row_number
            ),
            messages_reported_30d=integer(row, "messages_reported_30d", path, row_number),
        )


class CsvBusinessRepository(CsvRepository[Business], BusinessRepository):
    """Repository for `business_accounts.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "business_id",
                    "display_name",
                    "category",
                    "verified",
                    "official_domain",
                    "domain_used_by_sender",
                    "account_age_days",
                    "messages_sent_30d",
                    "user_reports_30d",
                    "domain_used_by_sender_age_days",
                ),
            ),
            lambda item: item.business_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> Business:
        path = self.table.path
        return Business(
            business_id=required_text(row, "business_id", path, row_number),
            display_name=required_text(row, "display_name", path, row_number),
            brand_name=text(row, "brand_name", path, row_number),
            category=enum_value(row, "category", BusinessCategory, path, row_number),
            verified=boolean(row, "verified", path, row_number),
            official_domain=text(row, "official_domain", path, row_number),
            domain_used_by_sender=text(row, "domain_used_by_sender", path, row_number),
            account_age_days=integer(row, "account_age_days", path, row_number),
            messages_sent_30d=integer(row, "messages_sent_30d", path, row_number),
            reports_30d=integer(row, "user_reports_30d", path, row_number),
            domain_used_by_sender_age_days=integer(
                row, "domain_used_by_sender_age_days", path, row_number
            ),
        )


class CsvGroupRepository(CsvRepository[Group], GroupRepository):
    """Repository for `groups.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "group_id",
                    "group_name",
                    "group_type",
                    "member_count",
                    "admin_count",
                    "created_at",
                    "messages_30d",
                ),
            ),
            lambda item: item.group_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> Group:
        path = self.table.path
        return Group(
            group_id=required_text(row, "group_id", path, row_number),
            display_name=required_text(row, "group_name", path, row_number),
            group_type=required_text(row, "group_type", path, row_number),
            member_count=integer(row, "member_count", path, row_number),
            admin_count=integer(row, "admin_count", path, row_number),
            created_at=timestamp(row, "created_at", path, row_number),
            messages_30d=integer(row, "messages_30d", path, row_number),
        )


class CsvGroupMembershipRepository(CsvRepository[GroupMembership], GroupMembershipRepository):
    """Repository for `group_members.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "group_id",
                    "user_id",
                    "role",
                    "joined_at",
                    "messages_sent_30d",
                    "messages_read_30d",
                    "replies_sent_30d",
                    "notifications_dismissed_30d",
                    "group_muted_by_user",
                ),
            ),
            lambda item: item.membership_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> GroupMembership:
        path = self.table.path
        group_id = required_text(row, "group_id", path, row_number)
        user_id = required_text(row, "user_id", path, row_number)
        return GroupMembership(
            membership_id=f"{group_id}:{user_id}",
            group_id=group_id,
            user_id=user_id,
            role=required_text(row, "role", path, row_number),
            joined_at=timestamp(row, "joined_at", path, row_number),
            messages_sent_30d=integer(row, "messages_sent_30d", path, row_number),
            messages_read_30d=integer(row, "messages_read_30d", path, row_number),
            replies_sent_30d=integer(row, "replies_sent_30d", path, row_number),
            notifications_dismissed_30d=integer(
                row, "notifications_dismissed_30d", path, row_number
            ),
            group_muted_by_user=boolean(row, "group_muted_by_user", path, row_number),
        )

    def for_user(self, user_id: str) -> tuple[GroupMembership, ...]:
        """Return memberships for one user."""
        return tuple(item for item in self.list() if item.user_id == user_id)

    def for_group(self, group_id: str) -> tuple[GroupMembership, ...]:
        """Return members for one group."""
        return tuple(item for item in self.list() if item.group_id == group_id)


class CsvConversationRepository(CsvRepository[Conversation], ConversationRepository):
    """Read normalized conversation envelopes from `messages.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "message_id",
                    "user_id",
                    "conversation_type",
                    "group_id",
                    "business_id",
                    "sender_user_id",
                ),
            ),
            lambda item: item.conversation_id,
        )

    def _items(self) -> tuple[Conversation, ...]:
        """Deduplicate naturally repeated conversations while preserving order."""
        if self._items_cache is None:
            seen: dict[str, Conversation] = {}
            for row_number, row in enumerate(self.table.rows(), start=2):
                path = self.table.path
                conversation_id = _conversation_id(row, path, row_number)
                if conversation_id in seen:
                    continue
                seen[conversation_id] = Conversation(
                    conversation_id=conversation_id,
                    conversation_type=_conversation_type(row, path, row_number),
                    user_id=required_text(row, "user_id", path, row_number),
                    group_id=text(row, "group_id", path, row_number),
                    business_id=text(row, "business_id", path, row_number),
                    participant_user_ids=tuple(
                        value
                        for value in (
                            text(row, "user_id", path, row_number),
                            text(row, "sender_user_id", path, row_number),
                        )
                        if value is not None
                    ),
                )
            self._items_cache = tuple(seen.values())
            self._index_cache = seen
        return self._items_cache

    def _parse_row(self, row: dict[str, object], row_number: int) -> Conversation:
        raise NotImplementedError("conversation rows are assembled by _items")

    def for_user(self, user_id: str) -> tuple[Conversation, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)


class CsvMediaRepository(MediaRepository):
    """Repository combining configured image and voice-note reference tables."""

    def __init__(self, images_path: Path, voice_notes_path: Path) -> None:
        self.images = CsvTable(images_path, ("image_id", "file_path"))
        self.voice_notes = CsvTable(voice_notes_path, ("voice_note_id", "file_path"))
        self._cache: tuple[Media, ...] | None = None
        self._index: dict[str, Media] | None = None

    @property
    def is_loaded(self) -> bool:
        """Return whether both media tables have been converted."""
        return self._cache is not None

    def _items(self) -> tuple[Media, ...]:
        if self._cache is None:
            items: list[Media] = []
            index: dict[str, Media] = {}
            for table, identifier, media_type in (
                (self.images, "image_id", MediaType.IMAGE),
                (self.voice_notes, "voice_note_id", MediaType.VOICE),
            ):
                for row_number, row in enumerate(table.rows(), start=2):
                    media = Media(
                        media_id=required_text(row, identifier, table.path, row_number),
                        media_type=media_type,
                        file_path=required_text(row, "file_path", table.path, row_number),
                    )
                    if media.media_id in index:
                        raise DuplicateRecordError(table.path, "media_id", media.media_id)
                    items.append(media)
                    index[media.media_id] = media
            self._cache = tuple(items)
            self._index = index
        return self._cache

    def get(self, record_id: str) -> Media | None:
        self._items()
        assert self._index is not None
        return self._index.get(record_id)

    def get_many(self, record_ids: Sequence[str]) -> tuple[Media, ...]:
        return tuple(item for record_id in record_ids if (item := self.get(record_id)) is not None)

    def list(self) -> tuple[Media, ...]:
        return self._items()

    def exists(self, record_id: str) -> bool:
        return self.get(record_id) is not None


class CsvNotificationHistoryRepository(
    CsvRepository[NotificationHistory], NotificationHistoryRepository
):
    """Repository for `daily_notification_summary.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(path, ("user_id", "date", "notifications_sent", "notifications_dismissed")),
            lambda item: item.history_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> NotificationHistory:
        path = self.table.path
        date = timestamp(row, "date", path, row_number)
        assert date is not None
        user_id = required_text(row, "user_id", path, row_number)
        return NotificationHistory(
            history_id=f"{user_id}:{date.date().isoformat()}",
            user_id=user_id,
            created_at=date,
            dismissed=integer(row, "notifications_dismissed", path, row_number) > 0,
            notifications_sent=integer(row, "notifications_sent", path, row_number),
            notifications_dismissed=integer(row, "notifications_dismissed", path, row_number),
        )

    def for_user(self, user_id: str) -> tuple[NotificationHistory, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)

    def between(self, start: datetime, end: datetime) -> tuple[NotificationHistory, ...]:
        return tuple(
            item
            for item in self.list()
            if item.created_at is not None and start <= item.created_at <= end
        )


class CsvInteractionHistoryRepository(
    CsvRepository[InteractionHistory], InteractionHistoryRepository
):
    """Repository for `message_events.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path,
                (
                    "user_id",
                    "message_id",
                    "message_opened",
                    "message_replied",
                    "reaction_time_minutes",
                    "notification_dismissed",
                    "muted_after_message",
                    "message_reported",
                ),
            ),
            lambda item: item.interaction_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> InteractionHistory:
        path = self.table.path
        user_id = required_text(row, "user_id", path, row_number)
        message_id = required_text(row, "message_id", path, row_number)
        return InteractionHistory(
            interaction_id=f"{user_id}:{message_id}",
            user_id=user_id,
            message_id=message_id,
            message_opened=boolean(row, "message_opened", path, row_number),
            message_replied=boolean(row, "message_replied", path, row_number),
            reaction_time_minutes=integer(
                row, "reaction_time_minutes", path, row_number, default=0
            ),
            notification_dismissed=boolean(row, "notification_dismissed", path, row_number),
            muted_after_message=boolean(row, "muted_after_message", path, row_number),
            message_reported=boolean(row, "message_reported", path, row_number),
        )

    def for_user(self, user_id: str) -> tuple[InteractionHistory, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)

    def for_message(self, message_id: str) -> tuple[InteractionHistory, ...]:
        return tuple(item for item in self.list() if item.message_id == message_id)

    def between(self, start: datetime, end: datetime) -> tuple[InteractionHistory, ...]:
        return ()


class CsvMessageEventRepository(CsvRepository[MessageEvent], MessageEventRepository):
    """Backward-compatible repository for raw message event rows."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(path, ("user_id", "message_id", "message_opened", "message_replied")),
            lambda item: f"{item.user_id}:{item.message_id}",
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> MessageEvent:
        path = self.table.path
        return MessageEvent(
            user_id=required_text(row, "user_id", path, row_number),
            message_id=required_text(row, "message_id", path, row_number),
            message_opened=boolean(row, "message_opened", path, row_number),
            message_replied=boolean(row, "message_replied", path, row_number),
            reaction_time_minutes=integer(
                row, "reaction_time_minutes", path, row_number, default=0
            ),
            notification_dismissed=boolean(row, "notification_dismissed", path, row_number),
            muted_after_message=boolean(row, "muted_after_message", path, row_number),
            message_reported=boolean(row, "message_reported", path, row_number),
        )

    def for_user(self, user_id: str) -> tuple[MessageEvent, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)

    def for_message(self, message_id: str) -> tuple[MessageEvent, ...]:
        return tuple(item for item in self.list() if item.message_id == message_id)


class CsvBusinessHistoryRepository(CsvRepository[BusinessHistory], BusinessHistoryRepository):
    """Repository for `user_business_history.csv`."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            CsvTable(
                path, ("user_id", "business_id", "why_user_knows_account", "last_activity_at")
            ),
            lambda item: item.history_id,
        )

    def _parse_row(self, row: dict[str, object], row_number: int) -> BusinessHistory:
        path = self.table.path
        user_id = required_text(row, "user_id", path, row_number)
        business_id = required_text(row, "business_id", path, row_number)
        return BusinessHistory(
            history_id=f"{user_id}:{business_id}",
            user_id=user_id,
            business_id=business_id,
            why_user_knows_account=text(row, "why_user_knows_account", path, row_number),
            last_interaction_at=timestamp(
                row, "last_activity_at", path, row_number, required=False
            ),
            opted_in=boolean(row, "allows_promotions", path, row_number),
            opted_out=text(row, "promotions_opted_out_at", path, row_number) is not None,
            order_count=integer(row, "activity_count_180d", path, row_number),
            activity_count_180d=integer(row, "activity_count_180d", path, row_number),
            messages_opened_30d=integer(row, "messages_opened_30d", path, row_number),
            messages_dismissed_30d=integer(row, "messages_dismissed_30d", path, row_number),
            messages_replied_30d=integer(row, "messages_replied_30d", path, row_number),
            last_reply_at=timestamp(row, "last_reply_at", path, row_number, required=False),
        )

    def for_user(self, user_id: str) -> tuple[BusinessHistory, ...]:
        return tuple(item for item in self.list() if item.user_id == user_id)

    def for_business(self, business_id: str) -> tuple[BusinessHistory, ...]:
        return tuple(item for item in self.list() if item.business_id == business_id)
