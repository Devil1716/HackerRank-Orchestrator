# Cortex Notify Interview Guide

## Architecture walkthrough

The system starts with typed Polars repositories, builds a complete `MessageContext`, derives deterministic personalization and evidence metadata, retrieves historical candidates, computes 25 features, aggregates them into 10 signals, and assembles a `DecisionPacket`. Only then does the Router Agent produce a structured `Decision`, which validation converts into an exact CSV row.

## Module-by-module explanation

- `repositories`: read-only dataset adapters and schema/error handling.
- `context`: joins message, user, conversation, history, business, group, and media metadata.
- `personalization`: immutable deterministic user profiles.
- `retrieval`: isolated embedding, vector, reranking, and evidence ports.
- `features`: explainable normalized feature calculations.
- `priority`: compact weighted signals for reasoning.
- `orchestration`: packet assembly, metadata, and trace.
- `router`: provider-neutral prompt, validation, repair, and decision boundary.
- `pipeline`: batch execution, fallback validation, metrics, and CSV export.

## Design rationale

The LLM is deliberately not the center of the architecture. Deterministic preprocessing makes inputs reproducible, reduces prompt size, preserves provenance, and makes failures diagnosable. One agent avoids multi-agent coordination and hidden policy.

## Failure modes

Missing datasets fail with typed repository errors. Malformed provider JSON gets one repair attempt and then fails explicitly. Invalid decisions receive a safe mute fallback. Missing optional context remains valid with reduced confidence. Output is written only after model validation.

## Scalability

The repository and vector-store ports permit PostgreSQL/Qdrant migration. Batch processing exposes a future parallel boundary. Immutable packets make retries and replay safe.

## Security

No secrets are committed. Provider credentials are injected through environment/configuration. The Router Agent cannot access repositories or raw files. Logs should be reviewed before production to ensure message content is not emitted by custom providers.

## Performance and cost

Lazy repository loading, bounded retrieval caches, batch embeddings, prompt budgets, and metrics reduce cost. The local 110-message benchmark runs at roughly 42 messages/second with the Mock provider; external provider latency and cost must be measured separately.

## Production deployment

The container is intentionally small and stateless. Mount datasets read-only,
mount the output directory explicitly, inject provider secrets through the
environment, and ship structured logs to the platform collector. A production
deployment should add resource limits, health probes, retry budgets, and a
separate secrets manager; none of those operational controls are required by
the offline judge path.

## Whiteboard explanation

Draw four boundaries left to right: repositories, deterministic preparation,
DecisionPacket, and Router/validation. Put the data contract under the first
three boundaries and show one arrow into the Router. Explain that every arrow
is typed, provenance-carrying, and replayable. This quickly communicates why
the model is replaceable while the decision system remains stable.

## Observability

Structured events identify repository queries, stage durations, signal
aggregation, packet creation, provider calls, validation, and export. Trace IDs
connect packet construction to the final decision. Sensitive message content is
not required in operational logs.

## Likely questions and ideal answers

**Why not let the LLM read the CSVs?** Because that would make behavior opaque, non-reproducible, and difficult to secure. The model receives a validated packet.

**How do you handle hallucination?** The prompt forbids invented facts, evidence IDs are constrained by the packet, and output is schema-validated with a bounded repair path.

**Why immutable models?** They prevent downstream mutation of evidence and make traces/replays trustworthy.

**How would you scale retrieval?** Replace the vector-store adapter with a managed store while retaining the retriever contracts and packet schema.

**How do you calibrate confidence?** Compare confidence buckets against matched gold labels; the current visible fixture is useful for smoke testing but does not label the full production dataset.

**What is the safest failure action?** `mute` with zero confidence and an explicit fallback reason, because an invalid AI output must not silently interrupt users.
