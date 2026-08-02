"""Provider and storage abstractions for retrieval."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.models import MessageContext, PersonalizationProfile


class EmbeddingProvider(ABC):
    """Generate vectors without exposing a provider implementation."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Embed a batch of texts."""
        raise NotImplementedError


class VectorStore(ABC):
    """Searchable vector index abstraction."""

    @abstractmethod
    def add(self, ids: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        """Add vectors to the index."""
        raise NotImplementedError

    @abstractmethod
    def search(self, vector: Sequence[float], limit: int) -> tuple[tuple[str, float], ...]:
        """Return ID and similarity pairs."""
        raise NotImplementedError


class Reranker(ABC):
    """Optional isolated cross-encoder reranking boundary."""

    @abstractmethod
    def rerank(self, query: str, candidates: Sequence[str]) -> tuple[float, ...]:
        """Return one normalized score per candidate."""
        raise NotImplementedError


class Retriever(ABC):
    """A context-only independent retriever."""

    name: str

    @abstractmethod
    def retrieve(
        self,
        context: MessageContext,
        profile: PersonalizationProfile,
        limit: int,
    ) -> tuple["RetrievalCandidate", ...]:
        """Return candidates without accessing repositories."""
        raise NotImplementedError


class RetrievalCandidate:
    """Structural candidate contract used internally by retrievers."""

    def __init__(self, evidence_id: str, summary: str, similarity: float, reason: str) -> None:
        self.evidence_id = evidence_id
        self.summary = summary
        self.similarity = similarity
        self.reason = reason
