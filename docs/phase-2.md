# Cortex Notify Phase 2 — Repository Layer

## Architecture

Repositories are the only layer that reads dataset files. The public boundary
returns immutable Pydantic models and tuples; no caller receives a Polars
`DataFrame`, `LazyFrame`, CSV path, or raw row.

```text
Settings -> repository factory -> repository interfaces -> domain models
                                  └-> private Polars CSV adapter
```

Each CSV repository owns one logical dataset. Media is the one deliberate
two-file adapter because images and voice notes are two source tables for the
single `MediaRepository` contract. Group metadata and group membership are
separate repositories. Conversations are normalized from the
message source because the supplied data has no conversation ID column.

## Data flow

1. `Settings.dataset_path()` resolves each file from configuration.
2. The factory constructs read-only repository objects without reading files.
3. The first repository access creates a `polars.scan_csv` lazy frame.
4. Required columns are checked before records are converted.
5. Rows are normalized into immutable domain models.
6. A primary-key index and immutable tuple cache serve subsequent lookups.

The domain mapping interprets timezone-less challenge timestamps as UTC. This
is storage normalization, not notification policy.

## Caching and indexing

Repositories use lazy construction, then collect each owned dataset once on
first access. Typed tuples avoid exposing mutable tabular state, while a
private dictionary provides O(1) primary-key lookup and repeated lookup reuse.
Batch lookup preserves caller ID order and omits missing IDs. Secondary
lookups filter the cached typed tuple, avoiding repeated CSV scans and
unnecessary Polars copies for the supplied dataset sizes.

## Error handling

Missing files, invalid schemas, duplicate primary keys, malformed records, and
malformed timestamps raise typed repository exceptions. Empty files with valid
headers return empty tuples. Records are never silently discarded or replaced
with fallback values.

## Performance and migration

The adapter uses Polars exclusively and keeps Polars private to the repository
layer. The repository interfaces are storage-neutral, so a future PostgreSQL
implementation can replace the CSV factory while preserving the same typed
methods and domain models. SQL adapters should retain the same primary-key,
ordering, missing-record, and error semantics.

## Scope boundary

Phase 2 does not build the Context Builder. It does not perform retrieval,
personalization, feature engineering, scoring, reasoning, LLM calls, OCR,
Whisper/ASR, or output generation.
