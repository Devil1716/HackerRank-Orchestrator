"""Stage and pipeline contracts with lifecycle logging hooks."""

from collections.abc import Sequence
from typing import Protocol, TypeVar

from app.models import Context, Decision, Message, OutputRow

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)


class PipelineStage(Protocol[InputT, OutputT]):
    """One replaceable, single-responsibility stage."""

    name: str

    def run(self, value: InputT) -> OutputT:
        """Transform one typed value."""
        ...


class MessageStage(PipelineStage[Message, Message], Protocol):
    """Stage that transforms or validates an incoming message."""


class ContextStage(PipelineStage[Message, Context], Protocol):
    """Stage that assembles context for one message."""


class DecisionStage(PipelineStage[Context, Decision], Protocol):
    """Stage that produces a domain decision."""


class ExportStage(Protocol):
    """Stage that converts decisions to output rows."""

    name: str

    def run(self, decisions: Sequence[Decision]) -> Sequence[OutputRow]:
        """Convert validated decisions to output rows."""
        ...


class Pipeline(Protocol):
    """Top-level pipeline runner contract."""

    def run(self, messages: Sequence[Message]) -> Sequence[OutputRow]:
        """Run the configured stage graph."""
        ...
