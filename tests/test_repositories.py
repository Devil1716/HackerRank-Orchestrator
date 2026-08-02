"""Repository integration and failure-mode tests."""

from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import pytest

from app.config.settings import Settings
from app.models import Message
from app.services.container import build_container
from repositories.csv import CsvMessageRepository, CsvUserRepository
from repositories.factory import build_repositories
from utils.repository_errors import (
    DatasetNotFoundError,
    DuplicateRecordError,
    InvalidSchemaError,
    MalformedTimestampError,
)


def test_all_configured_repositories_load_real_datasets() -> None:
    """Every configured repository returns typed immutable collections."""
    repositories = build_repositories(Settings())

    assert len(repositories.messages.list()) == 110
    assert len(repositories.users.list()) == 54
    assert len(repositories.businesses.list()) == 110
    assert len(repositories.groups.list()) == 23
    assert len(repositories.group_memberships.list()) == 401
    assert len(repositories.conversations.list()) == 58
    assert len(repositories.media.list()) == 33
    assert len(repositories.notification_history.list()) == 756
    assert len(repositories.interaction_history.list()) == 412
    assert len(repositories.business_history.list()) == 106
    assert len(repositories.message_history.list()) == 412
    assert len(repositories.message_events.list()) == 412
    assert isinstance(repositories.messages.list(), tuple)
    assert all(isinstance(item, Message) for item in repositories.messages.list())


def test_primary_and_batch_lookups_preserve_requested_order() -> None:
    """Primary, existence, and batch operations use the cached typed index."""
    repository = build_repositories(Settings()).messages
    first = repository.get("msg_023")
    assert first is not None
    assert repository.exists("msg_023")
    assert not repository.exists("missing")
    assert [item.message_id for item in repository.get_many(["msg_091", "msg_023"])] == [
        "msg_091",
        "msg_023",
    ]
    assert repository.get("msg_023") is first


def test_message_filters_and_media_lookup() -> None:
    """User, conversation, time-range, and media lookups are typed."""
    repositories = build_repositories(Settings())
    messages = repositories.messages
    message = messages.get("msg_023")
    assert message is not None
    assert message in messages.for_user("u_002")
    assert message in messages.for_conversation(message.conversation_id)
    assert message in messages.between(
        datetime(2026, 7, 30, tzinfo=UTC), datetime(2026, 7, 31, tzinfo=UTC)
    )
    assert repositories.media.get("img_001") is not None
    assert repositories.media.get("vn_001") is not None


def test_history_queries_and_container_injection() -> None:
    """History lookups and DI construction remain repository-only operations."""
    repositories = build_repositories(Settings())
    assert repositories.business_history.for_user("u_001")
    assert repositories.business_history.for_business("business_001")
    assert repositories.group_memberships.for_user("u_001")
    assert repositories.group_memberships.for_group("group_001")
    assert repositories.interaction_history.for_user("u_011")
    assert repositories.interaction_history.for_message("message_0001")
    assert repositories.notification_history.for_user("u_001")

    container = build_container(Settings())
    assert container.message_repository.get("msg_023") is not None
    assert container.repositories.media.get("img_001") is not None


def test_repository_is_lazy_until_first_access() -> None:
    """Constructing a CSV repository does not read or collect its file."""
    repository = CsvMessageRepository(Path("dataset/messages.csv"))
    assert not repository.is_loaded
    assert not repository.table.is_loaded
    repository.get("msg_023")
    assert repository.is_loaded
    assert repository.table.is_loaded


def test_missing_file_has_typed_error(tmp_path: Path) -> None:
    """Missing datasets fail with a repository-specific exception."""
    with pytest.raises(DatasetNotFoundError):
        CsvUserRepository(tmp_path / "missing.csv").list()


def test_invalid_schema_has_typed_error(tmp_path: Path) -> None:
    """Missing required columns fail before model conversion."""
    path = tmp_path / "users.csv"
    path.write_text("wrong_column\nvalue\n", encoding="utf-8")
    with pytest.raises(InvalidSchemaError):
        CsvUserRepository(path).list()


def test_valid_empty_dataset_returns_empty_tuple(tmp_path: Path) -> None:
    """A valid header with no records is a supported repository state."""
    path = tmp_path / "empty_users.csv"
    path.write_text(
        "user_id,do_not_disturb_window,messages_opened_30d,messages_replied_30d,"
        "notifications_dismissed_30d,messages_reported_30d\n",
        encoding="utf-8",
    )
    assert CsvUserRepository(path).list() == ()


def test_duplicate_and_malformed_records_have_typed_errors(tmp_path: Path) -> None:
    """Duplicate keys and malformed timestamps are never silently dropped."""
    duplicate = tmp_path / "duplicate_users.csv"
    duplicate.write_text(
        "user_id,do_not_disturb_window,messages_opened_30d,messages_replied_30d,"
        "notifications_dismissed_30d,messages_reported_30d\n"
        "u_1,,0,0,0,0\nu_1,,0,0,0,0\n",
        encoding="utf-8",
    )
    with pytest.raises(DuplicateRecordError):
        CsvUserRepository(duplicate).list()

    malformed = tmp_path / "malformed_messages.csv"
    pl.DataFrame(
        {
            "message_id": ["m1"],
            "user_id": ["u1"],
            "conversation_type": ["personal"],
            "created_at": ["not-a-timestamp"],
            "message_text": ["hello"],
            "forwarded_count": [0],
        }
    ).write_csv(malformed)
    with pytest.raises(MalformedTimestampError):
        CsvMessageRepository(malformed).list()
