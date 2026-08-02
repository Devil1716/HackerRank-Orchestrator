"""Isolated reranking adapters."""

from collections.abc import Sequence
from typing import Any, cast

from retrieval.errors import RerankerError
from retrieval.ports import Reranker


class DeterministicReranker(Reranker):
    """Stable lexical reranker for tests and offline operation."""

    def rerank(self, query: str, candidates: Sequence[str]) -> tuple[float, ...]:
        query_terms = set(query.lower().split())
        return tuple(
            len(query_terms.intersection(set(candidate.lower().split()))) / max(len(query_terms), 1)
            for candidate in candidates
        )


class BGEReranker(Reranker):
    """Lazy BAAI/bge-reranker-base SentenceTransformers cross-encoder adapter."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self.model_name = model_name
        self._model: object | None = None

    def rerank(self, query: str, candidates: Sequence[str]) -> tuple[float, ...]:
        try:
            from sentence_transformers import CrossEncoder  # type: ignore[import-not-found]

            if self._model is None:
                self._model = CrossEncoder(self.model_name)
            scores = cast(Any, self._model).predict(
                [(query, candidate) for candidate in candidates]
            )
            return tuple(max(0.0, min(1.0, (float(score) + 1.0) / 2.0)) for score in scores)
        except Exception as error:
            raise RerankerError("BGE reranking failed") from error
