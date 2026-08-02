# ADR-0004: Deterministic feature engineering

## Status

Accepted for Phase 6.

## Decision

Compute explainable normalized features before reasoning. Each feature carries
provenance and algorithm metadata, and the immutable `DecisionFeatures` aggregate
is the sole output of the layer.

## Rationale

Deterministic features make decisions reproducible, testable, and inspectable.
Computing them before reasoning prevents hidden repository or retrieval access and
keeps later reasoning focused on interpretation. Explicit algorithms and versioned
metadata make threshold changes reviewable and support future offline evaluation.
