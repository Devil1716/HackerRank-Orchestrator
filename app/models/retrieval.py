"""Typed evidence contracts for future retrieval adapters."""

from app.models.base import DomainModel
from app.models.enums import EvidenceType, InteractionType
from app.models.value_objects import (
    ConfidenceScore,
    MessageID,
    NonNegativeCount,
    SimilarityScore,
    Timestamp,
    UserID,
)


class Evidence(DomainModel):
    """One traceable signal supporting a later decision."""

    evidence_id: MessageID
    evidence_type: EvidenceType
    source_message_id: MessageID | None = None
    summary: str
    relevance: SimilarityScore
    confidence: ConfidenceScore
    source_retriever: str = "unknown"
    rank: NonNegativeCount = 0
    reranker_score: SimilarityScore = 0.0
    reason_selected: str = ""


class EvidenceBundle(DomainModel):
    """An ordered collection of evidence."""

    items: tuple[Evidence, ...] = ()
    retrieval_confidence: ConfidenceScore = 0.0
    evidence_message_ids: tuple[MessageID, ...] = ()
    retrievers_used: tuple[str, ...] = ()
    candidate_count: NonNegativeCount = 0
    metadata: tuple[tuple[str, str], ...] = ()


class RetrievedMessage(DomainModel):
    """A historical message returned by a future retrieval port."""

    message_id: MessageID
    user_id: UserID
    content: str
    created_at: Timestamp
    similarity: SimilarityScore


class RetrievedBehavior(DomainModel):
    """A behavior signal returned by a future retrieval port."""

    user_id: UserID
    interaction_type: InteractionType
    frequency: NonNegativeCount
    confidence: ConfidenceScore


class RetrievedPreference(DomainModel):
    """A preference signal returned by a future retrieval port."""

    user_id: UserID
    key: str
    value: str
    confidence: ConfidenceScore
