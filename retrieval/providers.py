"""Embedding providers, including the production BGE adapter."""

import hashlib
import importlib
import math
from collections.abc import Sequence
from typing import Any, cast

from retrieval.errors import MissingEmbeddingError
from retrieval.ports import EmbeddingProvider


class HashEmbeddingProvider(EmbeddingProvider):
    """Small deterministic provider used for tests and offline cold starts."""

    def __init__(self, dimensions: int = 32) -> None:
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        result = []
        for text in texts:
            values = [0.0] * self.dimensions
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode()).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimensions
                values[index] += 1.0 if digest[4] % 2 else -1.0
            magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
            result.append(tuple(value / magnitude for value in values))
        return tuple(result)


class BGEEmbeddingProvider(EmbeddingProvider):
    """Lazy SentenceTransformers adapter for BAAI/bge-small-en-v1.5."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model_name = model_name
        self._model: object | None = None

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if self._model is None:
            try:
                SentenceTransformer = importlib.import_module(
                    "sentence_transformers"
                ).SentenceTransformer
            except ImportError as error:
                raise MissingEmbeddingError(
                    "sentence-transformers is required for BGE embeddings"
                ) from error
            self._model = SentenceTransformer(self.model_name)
        try:
            encoded = cast(Any, self._model).encode(list(texts), normalize_embeddings=True)
            return tuple(tuple(float(value) for value in row) for row in encoded)
        except Exception as error:
            raise MissingEmbeddingError("BGE embedding generation failed") from error
