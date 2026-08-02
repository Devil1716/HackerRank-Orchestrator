# Phase 5 — Retrieval Engine

The retrieval engine consumes only `MessageContext` and `PersonalizationProfile`.
It never imports repositories, reads CSV files, performs feature engineering, or
does reasoning. Three independent retrievers cover historical messages,
interaction behavior, and structured personalization knowledge.

The pipeline is candidate generation, isolated embedding search, metadata-aware
candidate construction, deduplication, cross-retriever merge, isolated reranking,
and immutable `EvidenceBundle` creation. Evidence retains source retriever, rank,
similarity, reranker score, and selection reason.

## Providers and performance

`BGEEmbeddingProvider` lazily loads `BAAI/bge-small-en-v1.5` through
SentenceTransformers. `FaissVectorStore` is the only class that imports FAISS;
the `VectorStore` port allows Qdrant migration without changing retrieval logic.
`BGEReranker` isolates `BAAI/bge-reranker-base`. The default DI graph uses small
deterministic providers for offline startup and tests. Embeddings are batched,
stores are created lazily by retrievers, and retrieval uses a bounded LRU cache.
Incremental indexing can be added behind `VectorStore.add`.

## Confidence

Confidence is deterministic: 40% mean embedding similarity, 25% mean reranker
agreement, 20% cross-retriever agreement, and 15% supporting-result count capped
at five results. Empty or cold-start inputs return zero confidence. Provider,
vector-store, reranker, and partial retrieval failures are typed at their
boundaries; no LLM is consulted.

## Why this design

Three retrievers keep message semantics, behavior signals, and structured user
knowledge independently testable. FAISS is an efficient local vector baseline;
BGE provides replaceable semantic representations. Retrieval precedes reasoning
so later reasoning receives traceable evidence rather than hidden data access.
Evidence bundles preserve provenance and enable validation. Feature Engineering,
Router Agent, OCR, Whisper, and Phase 6 are explicitly out of scope.
