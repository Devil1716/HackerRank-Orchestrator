# Phase 6 — Deterministic Feature Engineering

Feature Engineering consumes only `MessageContext`, `PersonalizationProfile`,
and `EvidenceBundle`. It never accesses repositories, performs retrieval, calls
an LLM, or invokes OCR/Whisper.

## Pipeline and contract

`FeatureEngineeringService` delegates to `FeaturePipeline`, which validates the
input, runs independently registered calculators, validates normalized outputs,
and returns immutable `DecisionFeatures`. Every `FeatureScore` includes its name,
inputs, algorithm version, confidence, and supporting evidence IDs.

All values are clamped to `[0, 1]`. The algorithm version is `phase6-v1`.

## Explicit algorithms

Counts use documented caps: conversation counts cap at 10/50, forwarded messages
cap at 5, evidence cap at 5, business history cap at 5, and notification
dismissal is dismissed/sent with a denominator minimum of one. Presence signals
are binary; optional missing inputs produce zero value and zero confidence where
appropriate. Temporal importance is 1.0 from 08:00 through 21:59 and 0.5
otherwise. Evidence strength is supporting evidence count / 5. Retrieval
confidence is copied from the bundle. These simple rules favor auditability and
cold-start safety over predictive sophistication.

The pipeline traverses each input collection at most once per calculator family,
does not mutate inputs, and is suitable for future batch orchestration. Logs emit
feature start/completion, algorithm version, confidence, duration, validation, and
pipeline completion.

Feature Engineering ends here. Router Agent and Phase 7 are not implemented.
