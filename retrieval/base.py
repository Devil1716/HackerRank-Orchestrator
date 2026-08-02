"""Retrieval boundary; no ranking or search implementation is included in Phase 0."""

from abc import ABC, abstractmethod

from app.models import Context, Evidence


class EvidenceRetriever(ABC):
    """Retrieve traceable evidence for a context."""

    @abstractmethod
    def retrieve(self, context: Context) -> tuple[Evidence, ...]:
        """Return evidence selected by a future deterministic adapter."""
        raise NotImplementedError
