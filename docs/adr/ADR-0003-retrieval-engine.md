# ADR-0003: Isolated retrieval engine

## Status

Accepted for Phase 5.

## Decision

Use three independent retrievers over context-local data, with provider ports for
SentenceTransformers embeddings, FAISS-compatible vector storage, and BGE
reranking. Merge into immutable, provenance-rich `EvidenceBundle` objects and
calculate confidence deterministically.

## Consequences

Retrieval remains independently testable and storage-neutral. Production can use
BGE and FAISS; tests and offline startup remain deterministic without model
downloads. The engine cannot discover data absent from its two inputs, which is
an intentional boundary before Feature Engineering and reasoning.
