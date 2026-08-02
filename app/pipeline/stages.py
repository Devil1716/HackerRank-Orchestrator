"""Named Phase 0 stage registry; business implementations are intentionally absent."""

from enum import StrEnum


class StageName(StrEnum):
    """Canonical processing order for future adapters."""

    LOAD = "load"
    VALIDATE = "validate"
    METADATA = "metadata"
    MEDIA = "media"
    RETRIEVAL = "retrieval"
    BEHAVIOR = "behavior"
    SCORING = "scoring"
    REASONING = "reasoning"
    DECISION_VALIDATION = "decision_validation"
    EXPORT = "export"
