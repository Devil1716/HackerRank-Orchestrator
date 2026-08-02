"""Typed production pipeline errors."""


class PipelineError(Exception):
    """Base pipeline error."""


class DecisionValidationError(PipelineError):
    """Router decision failed validation."""


class OutputValidationError(PipelineError):
    """Output row failed the official schema."""
