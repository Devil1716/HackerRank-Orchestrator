"""Application-facing Phase 4 personalization service."""

import structlog

from app.models import MessageContext, PersonalizationProfile
from personalization.base import PersonalizationService
from personalization.builders import PersonalizationBuilder


class DeterministicPersonalizationService(PersonalizationService):
    """Build profiles exclusively from the provided immutable MessageContext."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._builder = PersonalizationBuilder(logger)

    def build(self, context: MessageContext) -> PersonalizationProfile:
        return self._builder.build(context)
