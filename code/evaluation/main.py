"""Competition evaluation framework and report generator.

This module deliberately lives in the existing evaluation entry point so the
frozen production architecture is not extended.
"""

import csv
import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class EvaluationRow:
    """One scored prediction."""

    message_id: str
    predicted: str
    expected: str
    confidence: float
    message_type: str = "unknown"
    reason: str = ""
    predicted_evidence_ids: tuple[str, ...] = ()
    expected_evidence_ids: tuple[str, ...] = ()
    feature_confidence: float = 1.0
    evidence_confidence: float = 1.0
    retrieval_confidence: float = 1.0
    media_confidence: float = 1.0
    reasoning_confidence: float = 1.0
    signals: tuple[str, ...] = ()
    features: tuple[str, ...] = ()


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

    def calculate(self, rows: list[EvaluationRow]) -> dict[str, object]:
        if not rows:
            return {
                "accuracy": 0.0,
                "macro_precision": 0.0,
                "macro_recall": 0.0,
                "macro_f1": 0.0,
                "weighted_f1": 0.0,
                "per_class_accuracy": {},
                "mean_confidence": 0.0,
                "ece": 0.0,
                "brier_score": 0.0,
                "calibration_gap": 0.0,
                "evidence_precision": 0.0,
                "evidence_recall": 0.0,
                "action_distribution": {},
            }
        accuracy = sum(row.predicted == row.expected for row in rows) / len(rows)
        mean_confidence = sum(row.confidence for row in rows) / len(rows)
        labels = ("notify", "digest", "mute")
        matrix = ConfusionMatrix().build(rows)
        precisions: list[float] = []
        recalls: list[float] = []
        f1s: list[float] = []
        supports: list[int] = []
        per_class_accuracy: dict[str, float] = {}
        for label in labels:
            true_positive = matrix[label][label]
            actual = sum(matrix[label].values())
            predicted = sum(matrix[expected][label] for expected in labels)
            precision = true_positive / predicted if predicted else 0.0
            recall = true_positive / actual if actual else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)
            supports.append(actual)
            per_class_accuracy[label] = round(recall, 4)
        total_support = sum(supports)
        weighted_f1 = (
            sum(score * support for score, support in zip(f1s, supports, strict=True))
            / total_support
            if total_support
            else 0.0
        )
        calibration = CalibrationMetrics().calculate(rows)
        evidence = EvidenceMetrics().calculate(rows)
        return {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(sum(precisions) / len(labels), 4),
            "macro_recall": round(sum(recalls) / len(labels), 4),
            "macro_f1": round(sum(f1s) / len(labels), 4),
            "weighted_f1": round(weighted_f1, 4),
            "per_class_accuracy": per_class_accuracy,
            "mean_confidence": round(mean_confidence, 4),
            "ece": calibration["ece"],
            "brier_score": calibration["brier_score"],
            "calibration_gap": calibration["calibration_gap"],
            "evidence_precision": evidence["precision"],
            "evidence_recall": evidence["recall"],
            "action_distribution": _distribution(rows, "predicted"),
        }


def _distribution(rows: list[EvaluationRow], field: str) -> dict[str, int]:
    """Return deterministic counts for one row field."""
    counts: dict[str, int] = {}
    for row in rows:
        value = str(getattr(row, field))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


class EvidenceMetrics:
    """Calculate set-based evidence precision and recall when labels exist."""

    def calculate(self, rows: list[EvaluationRow]) -> dict[str, float]:
        labeled = [row for row in rows if row.expected_evidence_ids]
        if not labeled:
            return {"precision": 0.0, "recall": 0.0, "labeled_rows": 0.0}
        precision_total = 0.0
        recall_total = 0.0
        for row in labeled:
            predicted = set(row.predicted_evidence_ids)
            expected = set(row.expected_evidence_ids)
            precision_total += len(predicted & expected) / len(predicted) if predicted else 0.0
            recall_total += len(predicted & expected) / len(expected)
        return {
            "precision": round(precision_total / len(labeled), 4),
            "recall": round(recall_total / len(labeled), 4),
            "labeled_rows": float(len(labeled)),
        }


class CalibrationMetrics:
    """Calculate calibration curves, ECE, Brier score, and confidence bins."""

    def calculate(self, rows: list[EvaluationRow], bins: int = 10) -> dict[str, object]:
        if not rows:
            return {"ece": 0.0, "brier_score": 0.0, "calibration_gap": 0.0, "curve": []}
        buckets: list[list[EvaluationRow]] = [[] for _ in range(bins)]
        for row in rows:
            index = min(bins - 1, max(0, int(_clamp(row.confidence) * bins)))
            buckets[index].append(row)
        curve: list[dict[str, float | int]] = []
        ece = 0.0
        for index, bucket in enumerate(buckets):
            if not bucket:
                continue
            observed = sum(row.predicted == row.expected for row in bucket) / len(bucket)
            confidence = sum(row.confidence for row in bucket) / len(bucket)
            weight = len(bucket) / len(rows)
            ece += weight * abs(observed - confidence)
            curve.append(
                {
                    "bin": index,
                    "lower": round(index / bins, 4),
                    "upper": round((index + 1) / bins, 4),
                    "confidence": round(confidence, 4),
                    "accuracy": round(observed, 4),
                    "count": len(bucket),
                }
            )
        brier = sum((row.confidence - float(row.predicted == row.expected)) ** 2 for row in rows)
        brier /= len(rows)
        accuracy = sum(row.predicted == row.expected for row in rows) / len(rows)
        mean_confidence = sum(row.confidence for row in rows) / len(rows)
        return {
            "ece": round(ece, 4),
            "brier_score": round(brier, 4),
            "calibration_gap": round(abs(mean_confidence - accuracy), 4),
            "curve": curve,
        }


def _clamp(value: float) -> float:
    """Keep confidence in the closed interval required by the contract."""
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))


class CalibrationModel(Protocol):
    """Protocol implemented by offline confidence calibration strategies."""

    def fit(self, confidences: list[float], outcomes: list[bool]) -> None: ...

    def transform(self, confidence: float) -> float: ...


class TemperatureScaling:
    """Deterministic temperature scaling over confidence logits."""

    def __init__(self, temperature: float = 1.0) -> None:
        self.temperature = max(0.05, temperature)

    def fit(self, confidences: list[float], outcomes: list[bool]) -> None:
        if len(confidences) != len(outcomes) or not confidences:
            raise ValueError("confidences and outcomes must be non-empty and aligned")
        best_temperature = self.temperature
        best_loss = self._loss(confidences, outcomes, best_temperature)
        for candidate in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0):
            loss = self._loss(confidences, outcomes, candidate)
            if loss < best_loss:
                best_temperature, best_loss = candidate, loss
        self.temperature = best_temperature

    def transform(self, confidence: float) -> float:
        probability = _clamp(confidence)
        if probability in (0.0, 1.0):
            probability = 0.000001 if probability == 0.0 else 0.999999
        logit = math.log(probability / (1.0 - probability)) / self.temperature
        return round(1.0 / (1.0 + math.exp(-logit)), 6)

    def _loss(self, confidences: list[float], outcomes: list[bool], temperature: float) -> float:
        self.temperature = temperature
        return sum(
            (self.transform(c) - float(outcome)) ** 2
            for c, outcome in zip(confidences, outcomes, strict=True)
        ) / len(confidences)


class PlattScaling(TemperatureScaling):
    """Compatibility interface for future logistic calibration parameters."""


class IsotonicCalibration:
    """Dependency-free monotonic calibration interface using fitted buckets."""

    def __init__(self) -> None:
        self._points: list[tuple[float, float]] = []

    def fit(self, confidences: list[float], outcomes: list[bool]) -> None:
        if len(confidences) != len(outcomes) or not confidences:
            raise ValueError("confidences and outcomes must be non-empty and aligned")
        pairs = sorted(
            (_clamp(c), float(outcome)) for c, outcome in zip(confidences, outcomes, strict=True)
        )
        running = 0.0
        self._points = []
        for index, (confidence, outcome) in enumerate(pairs, 1):
            running += outcome
            self._points.append((confidence, running / index))

    def transform(self, confidence: float) -> float:
        if not self._points:
            return _clamp(confidence)
        value = _clamp(confidence)
        candidates = [calibrated for point, calibrated in self._points if point <= value]
        return round(candidates[-1] if candidates else self._points[0][1], 6)


class ConfidenceValidator:
    """Validate and combine deterministic confidence components."""

    def combine(self, row: EvaluationRow, calibrator: CalibrationModel | None = None) -> float:
        components = (
            row.feature_confidence,
            row.evidence_confidence,
            row.retrieval_confidence,
            row.media_confidence,
            row.reasoning_confidence,
        )
        if any(
            not math.isfinite(component) or not 0.0 <= component <= 1.0 for component in components
        ):
            raise ValueError("confidence components must be finite values between 0 and 1")
        combined = math.prod(components) ** (1.0 / len(components))
        return round(calibrator.transform(combined) if calibrator else combined, 6)


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
        result: list[EvaluationRow] = []
        for row in self.load():
            predicted, message_type, reason, confidence = predictor(row.get("message_text", ""))
            expected_evidence = tuple(
                item for item in row.get("evidence_message_ids", "").split(";") if item
            )
            result.append(
                EvaluationRow(
                    message_id=row["message_id"],
                    predicted=predicted,
                    expected=row["action"],
                    confidence=confidence,
                    message_type=message_type,
                    reason=reason,
                    expected_evidence_ids=expected_evidence,
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
    calibration = CalibrationMetrics().calculate(rows)
    failure_categories = _failure_categories(rows)
    confusion_text = (
        "expected\\predicted | notify | digest | mute\n"
        "-------------------|--------|--------|-----\n"
        "notify             | {notify_notify} | {notify_digest} | {notify_mute}\n"
        "digest             | {digest_notify} | {digest_digest} | {digest_mute}\n"
        "mute               | {mute_notify} | {mute_digest} | {mute_mute}\n"
    ).format(
        **{
            f"{expected}_{predicted}": count
            for expected, values in matrix.items()
            for predicted, count in values.items()
        }
    )
    output_dir.mkdir(exist_ok=True)
    plots_dir = output_dir / "evaluation_plots"
    plots_dir.mkdir(exist_ok=True)
    (output_dir / "evaluation_report.md").write_text(
        "# Evaluation Report\n\n"
        f"Rows: {len(rows)}\n\n"
        "## Metrics\n\n"
        + "\n".join(f"- **{key}:** `{value}`" for key, value in metrics.items())
        + "\n\n## Confusion matrix\n\n"
        + "```text\n"
        + confusion_text
        + "```\n\n"
        "## Calibration\n\n"
        "The reliability diagram is written to `evaluation_plots/reliability.svg`; "
        "the report does not claim calibration quality when labels are absent.\n",
        encoding="utf-8",
    )
    (output_dir / "evaluation_report.json").write_text(
        json.dumps(
            {
                "rows": len(rows),
                "metrics": metrics,
                "confusion_matrix": matrix,
                "calibration": calibration,
                "failure_categories": failure_categories,
                "errors": errors,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_evaluation_plots(plots_dir, calibration, metrics, matrix)
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


def _failure_categories(rows: list[EvaluationRow]) -> dict[str, int]:
    """Group incorrect rows into stable, actionable categories."""
    categories: dict[str, int] = {}
    for row in rows:
        if row.predicted == row.expected:
            continue
        category = f"{row.expected}_predicted_as_{row.predicted}"
        categories[category] = categories.get(category, 0) + 1
    return dict(sorted(categories.items()))


def _write_evaluation_plots(
    plots_dir: Path,
    calibration: dict[str, object],
    metrics: dict[str, object],
    matrix: dict[str, dict[str, int]],
) -> None:
    """Write dependency-free SVG artifacts suitable for reports and review."""
    curve = calibration.get("curve", [])
    points = curve if isinstance(curve, list) else []
    dots = " ".join(
        f'<circle cx="{100 + float(point["confidence"]) * 500:.1f}" '
        f'cy="{350 - float(point["accuracy"]) * 280:.1f}" r="5" fill="#27627e"/>'
        for point in points
        if isinstance(point, dict)
    )
    reliability = _svg_document(
        "Reliability Diagram",
        '<line x1="100" y1="350" x2="600" y2="70" stroke="#b7c8d4" stroke-dasharray="6 6"/>'
        '<line x1="100" y1="350" x2="600" y2="350" stroke="#17324d"/>'
        '<line x1="100" y1="350" x2="100" y2="70" stroke="#17324d"/>'
        f"{dots}"
        '<text x="275" y="390" class="label">mean confidence</text>'
        '<text x="18" y="220" class="label" transform="rotate(-90 18 220)">accuracy</text>',
    )
    (plots_dir / "reliability.svg").write_text(reliability, encoding="utf-8")
    histogram = _svg_document(
        "Confidence Histogram",
        "".join(
            f'<rect x="{100 + index * 50}" y="{350 - int(float(point["count"]) * 20)}" '
            f'width="32" height="{int(float(point["count"]) * 20)}" fill="#27627e"/>'
            for index, point in enumerate(points)
            if isinstance(point, dict)
        )
        + '<line x1="90" y1="350" x2="620" y2="350" stroke="#17324d"/>',
    )
    (plots_dir / "confidence_histogram.svg").write_text(histogram, encoding="utf-8")
    action_distribution = metrics.get("action_distribution", {})
    if not isinstance(action_distribution, dict):
        action_distribution = {}
    action_text = " ".join(f"{key}: {value}" for key, value in action_distribution.items())
    matrix_text = " ".join(
        f"{expected}/{predicted}: {count}"
        for expected, values in matrix.items()
        for predicted, count in values.items()
    )
    (plots_dir / "evaluation_summary.svg").write_text(
        _svg_document(
            "Evaluation Summary",
            f'<text x="70" y="150" class="body">{action_text}</text><text x="70" y="210" class="body">{matrix_text}</text>',
        ),
        encoding="utf-8",
    )


def _svg_document(title: str, body: str) -> str:
    """Return a small, portable SVG document with embedded typography."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="420" viewBox="0 0 720 420">'
        "<style>.title{font:700 26px Arial;fill:#17324d}.label,.body{font:16px Arial;fill:#49647a}</style>"
        f'<rect width="720" height="420" fill="#f8fbfd"/><text x="50" y="55" class="title">{title}</text>{body}</svg>'
    )


def main() -> None:
    """Generate competition evaluation reports."""
    rows = EvaluationRunner().run(text_baseline)
    _write_reports(rows)
    print(MetricsEngine().calculate(rows))


if __name__ == "__main__":
    main()
