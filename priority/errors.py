"""Typed Priority and Risk Engine errors."""


class PriorityRiskError(Exception):
    """Base engine error."""


class SignalValidationError(PriorityRiskError):
    """A generated signal violated its contract."""
