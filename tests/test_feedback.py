"""Offline feedback storage tests."""

from dataclasses import dataclass
from pathlib import Path

from feedback import FeedbackRecord, FeedbackStore, OfflineFeedbackLoop


@dataclass(frozen=True)
class Row:
    """Minimal dataclass-shaped row used to test offline replacement."""

    message_id: str
    expected: str


def test_feedback_round_trip_and_offline_override(tmp_path: Path) -> None:
    store = FeedbackStore(tmp_path / "feedback.jsonl")
    store.append(FeedbackRecord("m1", "notify", "mute", "user override"))

    records = store.list()
    rows = [Row("m1", "notify")]
    updated = OfflineFeedbackLoop().apply(rows, records)

    assert records[0].user_action == "mute"
    assert updated[0].expected == "mute"
