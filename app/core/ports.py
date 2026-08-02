"""Dependency-inversion contracts for adapters and services."""

from collections.abc import Iterable, Sequence
from typing import Protocol

from app.models import Context, Decision, Message, MessageContext, MessageHistory, OutputRow


class MessageRepository(Protocol):
    """Read incoming messages from any supported source."""

    def list_messages(self) -> Iterable[Message]:
        """Return incoming messages in source-defined order."""
        ...


class HistoryRepository(Protocol):
    """Retrieve user-scoped historical messages."""

    def find_for_message(self, message: Message, *, limit: int) -> Sequence[MessageHistory]:
        """Return the most relevant history for one incoming message."""
        ...


class ContextAssembler(Protocol):
    """Build a context object without prescribing storage technology."""

    def assemble(self, message: Message) -> MessageContext:
        """Assemble the immutable context for one message."""
        ...


class DecisionService(Protocol):
    """Evaluate context; implementations belong to later phases."""

    def decide(self, context: Context) -> Decision:
        """Return a validated decision for the supplied context."""
        ...


class OutputExporter(Protocol):
    """Persist validated output rows."""

    def export(self, rows: Sequence[OutputRow]) -> None:
        """Persist output rows to the configured destination."""
        ...
