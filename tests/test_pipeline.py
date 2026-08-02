"""Final Phase 8 pipeline tests."""

import csv
from pathlib import Path

from app.services.container import build_container
from pipeline.service import ExecutionPipeline


def test_end_to_end_batch_exports_exact_schema(tmp_path: Path) -> None:
    """A batch produces one valid row per incoming message."""
    container = build_container()
    ids = tuple(message.message_id for message in container.message_repository.list())
    path = ExecutionPipeline(container).export(ids, tmp_path / "output.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(ids)
    assert tuple(rows[0]) == (
        "message_id",
        "action",
        "message_type",
        "reason",
        "confidence",
        "evidence_message_ids",
    )


def test_empty_batch_is_valid(tmp_path: Path) -> None:
    """An empty valid input produces a header-only output."""
    container = build_container()
    path = ExecutionPipeline(container).export((), tmp_path / "empty.csv")
    assert path.read_text(encoding="utf-8").startswith("message_id,action,message_type")
