# ADR-0008: Production execution pipeline

## Status

Accepted as the final engineering phase.

## Decision

Compose the existing services in one `ExecutionPipeline`, validate every Router
decision before output, apply a safe deterministic fallback on validation failure,
and export the exact HackerRank CSV schema.

## Consequences

The complete system is runnable from one command and observable through structured
metrics and logs. Validation failures cannot silently corrupt output. Batch
processing is sequential today but exposes a boundary for future parallelism;
the architecture remains frozen after Phase 8.
