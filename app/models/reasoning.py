"""Reasoning input, decision, and trace contracts."""

from app.models.base import DomainModel
from app.models.contexts import NotificationContext
from app.models.enums import ActionType, MessageType
from app.models.features import FeatureScores
from app.models.personalization import PersonalizationProfile
from app.models.retrieval import EvidenceBundle
from app.models.value_objects import ConfidenceScore, MessageID, NonNegativeCount


class DecisionInput(DomainModel):
    """All structured inputs available to a future reasoning service."""

    context: NotificationContext
    personalization: PersonalizationProfile
    evidence: EvidenceBundle
    features: FeatureScores


class DecisionTrace(DomainModel):
    """Auditable explanation metadata for a decision."""

    steps: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    model_name: str | None = None


class Decision(DomainModel):
    """Final typed decision contract."""

    message_id: MessageID
    action: ActionType
    message_type: MessageType
    reason: str = ""
    confidence: ConfidenceScore
    trace: DecisionTrace = DecisionTrace()
    evidence_message_ids: tuple[MessageID, ...] = ()
    decision_version: str = "phase7-v1"
    prompt_version: str = "router-prompt-v1"
    provider: str = "unknown"
    latency_ms: float = 0.0
    token_usage: NonNegativeCount = 0
    repair_count: NonNegativeCount = 0
    estimated_cost: float = 0.0
