"""Reasoning interface isolated from every deterministic upstream component."""

from abc import ABC, abstractmethod

from app.models import Context, Decision


class ReasoningService(ABC):
    """Produce a decision from a fully prepared context."""

    @abstractmethod
    def decide(self, context: Context) -> Decision:
        """Return a decision using a future replaceable reasoning adapter."""
        raise NotImplementedError
