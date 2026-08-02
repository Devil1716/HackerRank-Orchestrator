# Phase 8 — Production Execution Pipeline

Phase 8 assembles the frozen architecture into one runnable path:

`messages.csv → repositories → context → personalization → retrieval → features → signals → DecisionPacket → Router Agent → validation → output.csv`.

`ExecutionPipeline` processes one message or a tuple of message IDs. `BatchProcessor`
keeps the interface streaming-friendly and leaves future parallel execution
behind the same boundary. `ValidationEngine` validates the immutable `Decision`
schema, action/message type, confidence, evidence references, versions, provider,
and execution metrics. Invalid decisions receive a deterministic mute/unknown
fallback and are logged.

`OutputGenerator` and `CSVExporter` emit exactly the six HackerRank columns in the
required order. Metrics collect message count, validation failures, repairs,
tokens, cost, latency, and stage timing. The CLI exposes `run`, `evaluate`,
`benchmark`, `validate`, `export`, and `profile`.

Deployment uses the existing settings/environment and repository paths. For
production provider credentials, inject a configured Router provider; the default
local composition remains the deterministic Mock provider. No architecture
stages are added after Phase 8.
