"""Append-only feedback artifacts with no online learning side effects."""

import json
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FeedbackRecord:
    """One user override captured for a future offline evaluation run."""

    message_id: str
    predicted_action: str
    user_action: str
    created_at: str
    reason: str = ""

    @classmethod
    def create(
        cls, message_id: str, predicted_action: str, user_action: str, reason: str = ""
    ) -> "FeedbackRecord":
        """Create a record with an explicit UTC capture timestamp."""
        return cls(
            message_id=message_id,
            predicted_action=predicted_action,
            user_action=user_action,
            created_at=datetime.now(UTC).isoformat(),
            reason=reason,
        )


class FeedbackStore:
    """Persist feedback as deterministic JSON Lines for offline analysis."""

    def __init__(self, path: Path) -> None:
        """Create a store backed by one JSON Lines file."""
        self.path = path

    def append(self, record: FeedbackRecord) -> None:
        """Append one immutable feedback record."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    def list(self) -> tuple[FeedbackRecord, ...]:
        """Read all records in file order."""
        if not self.path.exists():
            return ()
        records: list[FeedbackRecord] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                records.append(FeedbackRecord(**json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid feedback record at line {line_number}") from error
        return tuple(records)


class OfflineFeedbackLoop:
    """Join user overrides to predictions without mutating model behavior."""

    def apply(self, rows: list[Any], feedback: tuple[FeedbackRecord, ...]) -> list[Any]:
        """Return copied evaluation rows with offline expected-action overrides."""
        overrides = {record.message_id: record.user_action for record in feedback}
        return [replace(row, expected=overrides.get(row.message_id, row.expected)) for row in rows]
