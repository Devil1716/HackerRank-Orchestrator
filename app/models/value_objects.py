"""Reusable constrained scalar types shared by domain models."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, Field, StringConstraints


def _require_aware(value: datetime) -> datetime:
    """Reject naive timestamps at the model boundary."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include timezone information")
    return value


Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128)]
MessageID = Identifier
UserID = Identifier
BusinessID = Identifier
GroupID = Identifier
ConversationID = Identifier
EmbeddingID = Identifier
ConfidenceScore = Annotated[float, Field(ge=0.0, le=1.0)]
SimilarityScore = Annotated[float, Field(ge=0.0, le=1.0)]
NonNegativeCount = Annotated[int, Field(ge=0)]
Timestamp = Annotated[datetime, AfterValidator(_require_aware)]
