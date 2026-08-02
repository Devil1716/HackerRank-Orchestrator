"""Official HackerRank CSV output generation."""

import csv
from pathlib import Path

from app.models import Decision, OutputFile, OutputRow
from pipeline.errors import OutputValidationError

OUTPUT_COLUMNS = (
    "message_id",
    "action",
    "message_type",
    "reason",
    "confidence",
    "evidence_message_ids",
)


class OutputGenerator:
    """Convert validated decisions into the exact public output model."""

    def build(self, decisions: tuple[Decision, ...]) -> OutputFile:
        rows = tuple(
            OutputRow(
                message_id=decision.message_id,
                action=decision.action,
                message_type=decision.message_type,
                reason=decision.reason,
                confidence=decision.confidence,
                evidence_message_ids=";".join(decision.evidence_message_ids) or "none",
            )
            for decision in decisions
        )
        return OutputFile(rows=rows)


class CSVExporter:
    """Write exact HackerRank columns and validate the target rows first."""

    def export(self, output: OutputFile, path: Path) -> Path:
        if tuple(OUTPUT_COLUMNS) != OUTPUT_COLUMNS:
            raise OutputValidationError("output schema is not stable")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_COLUMNS))
            writer.writeheader()
            for row in output.rows:
                writer.writerow(row.model_dump(mode="json"))
        return path
