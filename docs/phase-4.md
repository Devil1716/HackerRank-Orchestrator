# Phase 4 — Personalization and Evidence

Phase 4 converts one immutable `MessageContext` into deterministic, immutable
personalization profiles. The layer has no repository, CSV, dataset, retrieval,
embedding, OCR, speech, LLM, feature-engineering, or notification-policy dependency.

## Flow

`MessageContext` → `ProfileFactory` components → `ProfileAggregationService` →
`EvidenceProfileBuilder` → `ProfileValidators` → `PersonalizationProfile`.

Relationship signals use explicit group metadata and membership roles. Behavior
uses interaction flags and timestamps. Preferences use the recipient's DND field,
group mute flags, conversation type, and business opt-out records. Topics use a
small deterministic keyword vocabulary over text already present in the context;
media content is never opened. Business trust is descriptive history aggregation,
not a policy decision.

Evidence is metadata only: IDs, counts, summaries, media references, and time
ranges. No content is retrieved or ranked.

## Determinism and immutability

All collections are tuples, all public outputs are frozen Pydantic models, and
sorting is applied wherever input order could otherwise affect output. Empty or
cold-start histories produce valid zero-valued profiles. The service receives no
repository object and cannot access datasets.

## Migration and boundaries

The Phase 4 contract is intentionally storage-neutral. A future PostgreSQL
adapter remains below the Phase 3 context builder and requires no personalization
changes. Phase 5 may consume these profiles for deterministic features and later
reasoning. Context Builder is not implemented or changed by Phase 4.
