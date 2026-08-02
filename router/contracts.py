"""Provider and prompt contracts."""

from abc import ABC, abstractmethod

from app.models import DecisionPacket


class ProviderResponse:
    """Provider output and usage metadata."""

    def __init__(self, content: str, token_usage: int = 0, provider: str = "unknown") -> None:
        self.content = content
        self.token_usage = token_usage
        self.provider = provider


class Provider(ABC):
    """Pluggable model provider boundary."""

    name: str

    @abstractmethod
    def complete(self, prompt: str) -> ProviderResponse:
        """Return structured reasoning text for one prompt."""
        raise NotImplementedError


class PromptComponent(ABC):
    """Independently testable prompt component."""

    @abstractmethod
    def build(self, packet: DecisionPacket) -> str:
        """Build one bounded prompt section."""
        raise NotImplementedError
