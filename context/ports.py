"""Public context-builder interfaces."""

from abc import ABC, abstractmethod

from app.models import Message, MessageContext


class ContextBuilder(ABC):
    """Build one complete immutable message context."""

    @abstractmethod
    def build(self, message: Message | str) -> MessageContext:
        """Build from an incoming message object or message ID."""
        raise NotImplementedError


class ContextProvider(ContextBuilder):
    """Backward-compatible name for the context-builder port."""
