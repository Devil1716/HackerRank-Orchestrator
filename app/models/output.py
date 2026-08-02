"""External output contract for later execution phases."""

from app.models.base import DomainModel
from app.models.enums import ActionType, MessageType
from app.models.value_objects import ConfidenceScore, MessageID


class OutputRow(DomainModel):
    """One serialized notification decision row."""

    message_id: MessageID
    action: ActionType
    message_type: MessageType
    reason: str
    confidence: ConfidenceScore
    evidence_message_ids: str


class OutputFile(DomainModel):
    """Validated collection of output rows."""

    rows: tuple[OutputRow, ...]
    filename: str = "output.csv"
