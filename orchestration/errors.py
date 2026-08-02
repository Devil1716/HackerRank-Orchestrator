"""Typed Decision Packet errors."""


class DecisionPacketError(Exception):
    """Base packet orchestration error."""


class DecisionPacketInputError(DecisionPacketError):
    """A required deterministic input is missing."""


class DecisionPacketValidationError(DecisionPacketError):
    """The assembled packet is incomplete or inconsistent."""
