# ADR-0005: Priority and Risk Engine

## Status

Accepted for Phase 6.5.

## Decision

Aggregate the 25 deterministic Phase 6 features into ten immutable, typed,
provenance-rich decision signals. Use explicit weighted averages and retain
structured reasons rather than passing the raw feature vector to later routing.

## Consequences

The future Router Agent receives a small stable contract and can explain every
signal from its source features. Weights are reviewable and versioned. The engine
does not itself choose an action, retrieve evidence, or access storage.
