# Cortex Notify Phase 0

## Frozen architecture

The repository is organized around deterministic data and service boundaries:

```text
context -> repositories -> personalization -> retrieval -> features
       -> media -> ocr / speech -> validation -> reasoning -> api
```

The arrows describe dependency direction, not execution order. `reasoning/`
is isolated and cannot own ingestion, retrieval, media extraction, or feature
engineering. No LangGraph, agent framework, classifier, model provider, or
business policy is installed.

## Root packages

- `models/` exposes the canonical typed domain entities.
- `config/` loads environment-backed settings.
- `repositories/` defines abstract storage ports.
- `context/` defines context assembly.
- `personalization/`, `retrieval/`, and `features/` define replaceable service
  contracts.
- `media/`, `ocr/`, and `speech/` isolate multimodal providers.
- `validation/` defines boundary validation.
- `reasoning/` defines the future decision service boundary.
- `api/` defines framework-neutral response payloads.
- `app/` owns startup, dependency injection, CLI, monitoring, and shared
  pipeline contracts.
- `tests/`, `docs/`, `scripts/`, `dataset/`, and `docker/` hold verification,
  documentation, operational tools, challenge data, and container assets.

## Phase 0 guarantees

- Configuration is validated before dependency construction.
- Domain models reject unknown fields and invalid ranges.
- Repository and service implementations are supplied later through abstract
  interfaces.
- Structured logs are JSON and stage-aware.
- Health checks are read-only.
- No Phase 0 module emits a prediction or applies routing policy.
