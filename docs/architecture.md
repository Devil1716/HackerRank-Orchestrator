# Architecture

## Scope

This repository is the production foundation for a multimodal notification
router. Phase 0 establishes contracts and operational boundaries only. There
is intentionally no routing heuristic, classifier, retrieval implementation,
OCR, ASR, LLM prompt, or decision policy yet.

## Dependency direction

```text
CLI / API adapters -> application services -> core ports -> domain models
                                      \-> infrastructure adapters (future)
```

The Pydantic models in `app/models` are the domain boundary. Ports in
`app/core/ports.py` and `app/pipeline/contracts.py` express what the system
needs without coupling it to CSV, a vector store, a model provider, or a media
library. `app/services/container.py` is the explicit composition root.

## Pipeline lifecycle

The canonical stage names are load, validate, metadata, media, retrieval,
behavior, scoring, reasoning, decision validation, and export. Each stage will
receive a typed value and return a typed value. Stage logging records
`message_id`, `stage`, `duration_ms`, `status`, and `errors` in JSON.

## Decisions deferred to later phases

- CSV/Polars ingestion and output adapters
- media content extraction (OCR and ASR)
- retrieval and evidence ranking
- behavior and risk features
- scoring, reasoning, and final action policy
- API/worker deployment topology

Keeping these behind ports allows each to be tested and replaced independently
without changing the domain contract or CLI.
