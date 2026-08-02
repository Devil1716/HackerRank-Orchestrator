# Production Enhancement Notes

This increment strengthens the frozen architecture without replacing any
pipeline stage.

## Evaluation and calibration

`code/evaluation/main.py` now reports accuracy, macro precision/recall/F1,
weighted F1, per-class accuracy, action distribution, confusion matrix,
evidence precision/recall, ECE, Brier score, calibration gap, and reliability
curve bins. It writes `docs/evaluation_report.json` and dependency-free SVG
artifacts under `docs/evaluation_plots/`.

Confidence calibration is offline and deterministic. `TemperatureScaling` is
the executable baseline; `PlattScaling` and `IsotonicCalibration` preserve
extension interfaces without adding a numerical dependency. `ConfidenceValidator`
combines feature, evidence, retrieval, media, and reasoning confidence using a
geometric mean before optional calibration.

## Policy and verification

`policy.PolicyEngine` evaluates safety, urgency, and quiet-hour directives
before reasoning and enforces them after the Router returns. The Router cannot
override a forced mute, digest, or notify action. `router.DecisionVerifier`
then checks reason and evidence consistency and applies a deterministic
high-spam safety correction.

Both boundaries are pure, dependency-injected through the Router composition,
and preserve the existing CLI and output schema.

## Offline feedback

`feedback.FeedbackStore` writes append-only JSON Lines records. `OfflineFeedbackLoop`
joins user overrides to evaluation rows only when an offline run explicitly
requests it; it never updates a live model or changes the online pipeline.

## Deliberately unimplemented infrastructure

The repository does not claim to include Redis, PostgreSQL, DuckDB, Parquet,
FAISS, Qdrant, Milvus, Kafka, RabbitMQ, OpenTelemetry, Whisper, or OCR runtime
adapters. Those are deployment-scale extensions that require infrastructure,
security, and benchmark decisions not present in the visible HackerRank
fixture. Existing ports remain the migration seams; no fake adapters or
unverified performance claims are added.
