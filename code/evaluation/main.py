"""Competition evaluation framework and report generator.

This module deliberately lives in the existing evaluation entry point so the
frozen production architecture is not extended.
"""

import csv
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationRow:
    """One scored prediction."""

    message_id: str
    predicted: str
    expected: str
    confidence: float
    message_type: str = "unknown"
    reason: str = ""


class ConfusionMatrix:
    """Build a multiclass action confusion matrix."""

    def build(self, rows: list[EvaluationRow]) -> dict[str, dict[str, int]]:
        labels = ("notify", "digest", "mute")
        matrix = {expected: {predicted: 0 for predicted in labels} for expected in labels}
        for row in rows:
            if row.expected in matrix and row.predicted in matrix[row.expected]:
                matrix[row.expected][row.predicted] += 1
        return matrix


class MetricsEngine:
    """Calculate accuracy, calibration, and validity metrics."""

    def calculate(self, rows: list[EvaluationRow]) -> dict[str, float]:
        if not rows:
            return {"accuracy": 0.0, "mean_confidence": 0.0, "calibration_gap": 0.0}
        accuracy = sum(row.predicted == row.expected for row in rows) / len(rows)
        mean_confidence = sum(row.confidence for row in rows) / len(rows)
        calibration_gap = abs(mean_confidence - accuracy)
        return {
            "accuracy": round(accuracy, 4),
            "mean_confidence": round(mean_confidence, 4),
            "calibration_gap": round(calibration_gap, 4),
        }


class PredictionComparator:
    """Compare two prediction collections by message ID."""

    def compare(self, left: list[EvaluationRow], right: list[EvaluationRow]) -> dict[str, int]:
        left_map = {row.message_id: row for row in left}
        right_map = {row.message_id: row for row in right}
        common = set(left_map) & set(right_map)
        return {
            "common": len(common),
            "changed_action": sum(
                left_map[key].predicted != right_map[key].predicted for key in common
            ),
            "changed_type": sum(
                left_map[key].message_type != right_map[key].message_type for key in common
            ),
        }


class ErrorAnalyzer:
    """Produce actionable records for incorrect predictions."""

    def analyze(self, rows: list[EvaluationRow]) -> list[dict[str, str]]:
        return [
            {
                "message_id": row.message_id,
                "prediction": row.predicted,
                "expected": row.expected,
                "confidence": str(row.confidence),
                "signals": "not available in solved sample fixture",
                "features": "not available in solved sample fixture",
                "evidence": "none",
                "reason": row.reason,
                "possible_cause": "text-only evaluation fixture lacks full packet labels",
                "recommended_fix": "evaluate with matched message IDs and packet-level annotations",
            }
            for row in rows
            if row.predicted != row.expected
        ]


class EvaluationRunner:
    """Run repeatable evaluation over the participant-visible solved fixture."""

    def __init__(self, sample_path: Path = Path("dataset/sample_messages.csv")) -> None:
        self.sample_path = sample_path

    def load(self) -> list[dict[str, str]]:
        with self.sample_path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def run(self, predictor: Callable[[str], tuple[str, str, str, float]]) -> list[EvaluationRow]:
        result = []
        for row in self.load():
            predicted, message_type, reason, confidence = predictor(row.get("message_text", ""))
            result.append(
                EvaluationRow(
                    message_id=row["message_id"],
                    predicted=predicted,
                    expected=row["action"],
                    confidence=confidence,
                    message_type=message_type,
                    reason=reason,
                )
            )
        return result


def text_baseline(text: str) -> tuple[str, str, str, float]:
    """Apply the competition baseline rules independently of production code."""
    lower = text.lower()
    if any(
        term in lower
        for term in ("otp", "password", "prize", "lottery", "click here", "verify account")
    ):
        return "mute", "scam", "suspicious language", 0.92
    if any(term in lower for term in ("sale", "discount", "offer", "promotion", "cashback")):
        return "digest", "promotion", "promotional content", 0.78
    if any(term in lower for term in ("payment", "invoice", "bill", "transaction", "due")):
        return "notify", "payment", "payment-related content", 0.84
    if any(
        term in lower
        for term in ("meeting", "schedule", "bus", "event", "deadline", "today", "tomorrow")
    ):
        return "notify", "event", "time-sensitive schedule content", 0.83
    return "digest", "unknown", "weak interruption signal", 0.61


def _write_reports(rows: list[EvaluationRow], output_dir: Path = Path("docs")) -> None:
    metrics = MetricsEngine().calculate(rows)
    matrix = ConfusionMatrix().build(rows)
    errors = ErrorAnalyzer().analyze(rows)
    output_dir.mkdir(exist_ok=True)
    (output_dir / "evaluation_report.md").write_text(
        "# Evaluation Report\n\n"
        f"Rows: {len(rows)}\n\nMetrics: `{metrics}`\n\n"
        f"Confusion matrix: `{matrix}`\n",
        encoding="utf-8",
    )
    (output_dir / "provider_comparison.md").write_text(
        "# Provider Comparison\n\n"
        "Mock is locally executable. OpenAI, Gemini, Ollama, and vLLM adapter seams require configured transports and credentials; no unverified accuracy ranking is claimed.\n",
        encoding="utf-8",
    )
    (output_dir / "prompt_report.md").write_text(
        "# Prompt Comparison\n\n"
        "Prompt versions remain versioned in the Router Agent. A matched gold set is required before claiming v1–v4 accuracy differences.\n",
        encoding="utf-8",
    )
    (output_dir / "retrieval_report.md").write_text(
        "# Retrieval Report\n\n"
        "Retrieval quality cannot be measured from sample labels alone because evidence relevance annotations are absent. Production telemetry exposes candidate counts, confidence, latency, and provenance.\n",
        encoding="utf-8",
    )
    (output_dir / "threshold_report.md").write_text(
        "# Threshold Report\n\n"
        "The current deterministic pipeline has explicit thresholds documented by phase. Threshold sweeps require packet-level gold labels; changing them without matched labels would risk overfitting.\n",
        encoding="utf-8",
    )
    (output_dir / "failure_analysis.md").write_text(
        "# Failure Analysis\n\n" + "\n".join(f"- `{error}`" for error in errors) + "\n",
        encoding="utf-8",
    )
    (output_dir / "performance_report.md").write_text(
        "# Performance Report\n\n"
        "The final pipeline is batch-capable and instrumented for stage latency, tokens, repairs, cost, and peak memory. Run `scripts/benchmark_pipeline.py` for local measurements.\n",
        encoding="utf-8",
    )


def main() -> None:
    """Generate competition evaluation reports."""
    rows = EvaluationRunner().run(text_baseline)
    _write_reports(rows)
    print(MetricsEngine().calculate(rows))


if __name__ == "__main__":
    main()
