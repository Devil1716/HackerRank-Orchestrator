"""Evaluation and confidence calibration tests."""

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def _evaluation_module() -> ModuleType:
    path = Path(__file__).parents[1] / "code" / "evaluation" / "main.py"
    spec = importlib.util.spec_from_file_location("evaluation_main", path)
    if spec is None or spec.loader is None:
        raise AssertionError("evaluation module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows(module: Any) -> list[Any]:
    return [
        module.EvaluationRow(
            message_id="m1",
            predicted="notify",
            expected="notify",
            confidence=0.9,
            predicted_evidence_ids=("e1",),
            expected_evidence_ids=("e1", "e2"),
        ),
        module.EvaluationRow(
            message_id="m2",
            predicted="mute",
            expected="digest",
            confidence=0.8,
            predicted_evidence_ids=("e3",),
            expected_evidence_ids=("e2",),
        ),
    ]


def test_metrics_include_class_and_evidence_quality() -> None:
    module = _evaluation_module()
    metrics = module.MetricsEngine().calculate(_rows(module))

    assert metrics["accuracy"] == 0.5
    assert metrics["macro_f1"] >= 0.0
    assert metrics["weighted_f1"] >= 0.0
    assert metrics["per_class_accuracy"]
    assert metrics["evidence_precision"] == 0.5
    assert metrics["evidence_recall"] == 0.25


def test_calibration_models_are_bounded_and_deterministic() -> None:
    module = _evaluation_module()
    temperatures = module.TemperatureScaling()
    temperatures.fit([0.2, 0.8, 0.9], [False, True, True])
    isotonic = module.IsotonicCalibration()
    isotonic.fit([0.2, 0.8, 0.9], [False, True, True])

    assert 0.0 <= temperatures.transform(0.75) <= 1.0
    assert 0.0 <= isotonic.transform(0.75) <= 1.0
    assert temperatures.transform(0.75) == temperatures.transform(0.75)


def test_confidence_validator_combines_five_components() -> None:
    module = _evaluation_module()
    row = module.EvaluationRow(
        message_id="m1",
        predicted="notify",
        expected="notify",
        confidence=0.9,
        feature_confidence=0.8,
        evidence_confidence=0.9,
        retrieval_confidence=0.7,
        media_confidence=1.0,
        reasoning_confidence=0.95,
    )

    combined = module.ConfidenceValidator().combine(row)
    assert 0.0 < combined < 1.0


def test_report_generator_writes_json_and_svg_artifacts(tmp_path: Path) -> None:
    module = _evaluation_module()
    module._write_reports(_rows(module), tmp_path)

    assert (tmp_path / "evaluation_report.json").exists()
    assert (tmp_path / "evaluation_plots" / "reliability.svg").exists()
    assert (tmp_path / "evaluation_plots" / "confidence_histogram.svg").exists()
