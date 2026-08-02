"""Phase 4 context-only personalization tests."""

import pytest
from pydantic import ValidationError

from app.services.container import build_container


def test_personalization_is_deterministic_and_immutable() -> None:
    """The same immutable context produces the same frozen profile."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    first = container.personalization_service.build(context)
    second = container.personalization_service.build(context)
    assert first == second
    assert first.user_id == context.recipient.user_id
    with pytest.raises(ValidationError):
        first.user_id = "other"  # type: ignore[misc]


def test_personalization_handles_cold_start_and_media_metadata_only() -> None:
    """Empty histories remain valid and media creates only a descriptor."""
    container = build_container()
    context = container.context_builder.build("msg_086")
    profile = container.personalization_service.build(context)
    assert profile.behavior is not None
    assert profile.behavior.open_rate == 0
    assert profile.evidence.descriptors[-1].media_ids == (context.media.media_id,)  # type: ignore[union-attr]
