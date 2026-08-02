# HackerRank Submission Notes

## Problem understanding

Cortex Notify routes each WhatsApp message to `notify`, `digest`, or `mute`. The decision must balance urgency, usefulness, risk, personalization, history, and evidence while returning the exact six-column CSV schema.

## Architecture

The frozen pipeline is repositories → context → personalization → retrieval → feature engineering → priority/risk → decision packet → Router Agent → validation → output. Repositories are the only dataset boundary. All pre-router stages are deterministic and immutable.

## Innovation

The system separates deterministic evidence construction from the one AI responsibility. Structured evidence, versioned features/signals, an immutable DecisionPacket, provenance, and strict output validation make the system explainable and debuggable.

## Engineering decisions and trade-offs

- Polars CSV adapters provide typed, lazy, replaceable access without Pandas.
- Pydantic frozen models prevent accidental stage mutation.
- Retrieval providers and vector stores are isolated for migration.
- Explicit deterministic fallbacks favor safety and reproducibility over silent partial output.
- The local Mock provider keeps the submission runnable without credentials; production transports are injectable.

## Deterministic preprocessing

Context, personalization, retrieval metadata, 25 features, 10 compact signals, and validation are deterministic. Confidence, evidence provenance, thresholds, and metadata are carried into the packet before reasoning.

## Why one Router Agent

The Router Agent has one narrow job: reason over a completed DecisionPacket. It cannot read CSVs, retrieve data, calculate scores, inspect media, or infer relationships. This minimizes hidden behavior and keeps evaluation reproducible.

## Production readiness

The project includes typed configuration, structured logs, DI, failure handling, safe fallback decisions, metrics, profiling, Docker packaging, CLI commands, tests, and exact CSV export.

## Scalability

Repositories and vector storage are replaceable, retrieval is isolated, and batch processing has a future parallelism boundary. Current execution is sequential to preserve deterministic ordering and simple operational behavior.

## Submission commands

```powershell
uv sync --extra dev
uv run orchestrate run --output output.csv
uv run orchestrate validate
uv run pytest
```
