"""FAISS-isolated and portable in-memory vector stores."""

import math
from collections.abc import Sequence

from retrieval.errors import CorruptVectorError, EmptyIndexError, VectorStoreError
from retrieval.ports import VectorStore


class InMemoryVectorStore(VectorStore):
    """Deterministic cosine store used as a dependency-injection default."""

    def __init__(self) -> None:
        self._vectors: dict[str, tuple[float, ...]] = {}

    def add(self, ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        if len(ids) != len(vectors):
            raise CorruptVectorError("IDs and vectors have different lengths")
        for identifier, vector in zip(ids, vectors, strict=True):
            values = tuple(float(value) for value in vector)
            if not values or any(not math.isfinite(value) for value in values):
                raise CorruptVectorError(f"invalid vector for {identifier}")
            self._vectors[identifier] = values

    def search(self, vector: Sequence[float], limit: int) -> tuple[tuple[str, float], ...]:
        if not self._vectors:
            raise EmptyIndexError("vector index is empty")
        query = tuple(float(value) for value in vector)
        if not query or any(not math.isfinite(value) for value in query):
            raise CorruptVectorError("invalid query vector")
        query_norm = math.sqrt(sum(value * value for value in query)) or 1.0
        scored = []
        for identifier, candidate in self._vectors.items():
            if len(candidate) != len(query):
                raise CorruptVectorError(f"dimension mismatch for {identifier}")
            norm = math.sqrt(sum(value * value for value in candidate)) or 1.0
            score = sum(left * right for left, right in zip(query, candidate, strict=True)) / (
                query_norm * norm
            )
            scored.append((identifier, max(0.0, min(1.0, (score + 1) / 2))))
        return tuple(sorted(scored, key=lambda item: (-item[1], item[0]))[:limit])


class FaissVectorStore(InMemoryVectorStore):
    """FAISS adapter boundary; import and index creation remain encapsulated."""

    def __init__(self) -> None:
        super().__init__()
        try:
            import faiss  # type: ignore[import-not-found]  # noqa: F401
        except ImportError as error:
            raise VectorStoreError("faiss-cpu is required for FaissVectorStore") from error
