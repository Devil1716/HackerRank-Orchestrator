"""Phase 3 Context Builder tests."""

from dataclasses import replace
from pathlib import Path
from typing import NoReturn

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.config.settings import Settings
from app.monitoring.logging import configure_logging
from app.services.container import build_container
from context.errors import RecipientNotFoundError, RepositoryQueryError
from context.service import ContextBuilderService
from repositories.factory import build_repositories
from utils.errors import RepositoryError


def test_direct_message_context_contains_required_relationships() -> None:
    """Direct messages resolve recipient, sender, history, and statistics."""
    context = build_container().context_builder.build("msg_091")
    assert context.message.message_id == "msg_091"
    assert context.recipient.user_id == "u_028"
    assert context.sender is not None
    assert context.conversation.conversation_type.value == "personal"
    assert context.conversation_statistics.message_count >= 1
    assert context.timestamps.message_created_at.tzinfo is not None


def test_group_message_context_contains_group_memberships() -> None:
    """Group messages resolve group metadata and participant membership."""
    context = build_container().context_builder.build("msg_005")
    assert context.group is not None
    assert context.group.group_id == "group_005"
    assert context.group_memberships
    assert context.group_statistics is not None
    assert context.group_statistics.membership_count == len(context.group_memberships)


def test_business_and_media_contexts_are_metadata_only() -> None:
    """Business and media records are assembled without content interpretation."""
    business = build_container().context_builder.build("msg_065")
    voice = build_container().context_builder.build("msg_086")
    assert business.business is not None
    assert business.business.business_id == "business_067"
    assert business.business_statistics is not None
    assert business.media is not None
    assert business.media.media_type.value == "image"
    assert voice.media is not None
    assert voice.media.media_type.value == "voice"


def test_missing_optional_media_is_logged_but_does_not_fail() -> None:
    """Missing optional media metadata produces a valid context."""
    container = build_container()
    message = container.message_repository.get("msg_005")
    assert message is not None
    changed = message.model_copy(update={"media_id": "missing-media"})
    context = container.context_builder.build(changed)
    assert context.media is None


def test_missing_recipient_is_a_context_error() -> None:
    """A missing required recipient cannot produce a context."""
    container = build_container()
    message = container.message_repository.get("msg_091")
    assert message is not None
    changed = message.model_copy(update={"user_id": "missing-user"})
    with pytest.raises(RecipientNotFoundError):
        container.context_builder.build(changed)


def test_repository_failure_is_wrapped() -> None:
    """Repository failures are translated to Context Builder errors."""

    class FailingMessageRepository:
        def get(self, record_id: str) -> NoReturn:
            raise RepositoryError("simulated failure")

    repositories = replace(build_repositories(Settings()), messages=FailingMessageRepository())
    configure_logging("INFO")
    service = ContextBuilderService(repositories, Settings(), build_container().logger)
    with pytest.raises(RepositoryQueryError):
        service.build("msg_091")


def test_context_is_immutable_and_builder_is_injected(tmp_path: Path) -> None:
    """The DI container supplies the builder and the result is frozen."""
    container = build_container(Settings(data_directory=Path("dataset"), output_directory=tmp_path))
    context = container.context_builder.build("msg_091")
    with pytest.raises(PydanticValidationError):
        context.recipient = context.recipient  # type: ignore[misc]
