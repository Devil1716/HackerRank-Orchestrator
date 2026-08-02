"""Deterministic personalization boundary."""

from abc import ABC, abstractmethod

from app.models import MessageContext, PersonalizationProfile


class PersonalizationService(ABC):
    """Build a profile from one immutable context and nothing else."""

    @abstractmethod
    def build(self, context: MessageContext) -> PersonalizationProfile:
        """Return a deterministic profile using only context fields."""
        raise NotImplementedError

    def enrich(self, context: MessageContext) -> PersonalizationProfile:
        """Backward-compatible spelling for profile construction."""
        return self.build(context)
