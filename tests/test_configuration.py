"""Configuration behavior tests."""

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_settings_accept_valid_thresholds() -> None:
    """Accept a valid lower/upper threshold pair."""
    settings = Settings(notify_threshold=0.8, mute_threshold=0.2)
    assert settings.notify_threshold == 0.8


def test_settings_reject_inverted_thresholds() -> None:
    """Reject thresholds that make the action bands ambiguous."""
    with pytest.raises(ValidationError):
        Settings(notify_threshold=0.2, mute_threshold=0.8)
