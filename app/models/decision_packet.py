"""Immutable orchestration packet and execution trace contracts."""

from datetime import datetime

from app.models.base import DomainModel
from app.models.contexts import MessageContext
from app.models.features import DecisionFeatures
from app.models.personalization import PersonalizationProfile
from app.models.retrieval import EvidenceBundle
from app.models.signals import DecisionSignals


class TraceStage(DomainModel):
    """One deterministic orchestration stage observation."""

    component: str
    started_at: datetime
    ended_at: datetime
    duration_ms: float
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class TraceMetadata(DomainModel):
    """Complete immutable execution trace."""

    stages: tuple[TraceStage, ...] = ()
    trace_id: str


class FeatureMetadata(DomainModel):
    """Feature-engineering provenance copied into the packet."""

    algorithm_version: str
    feature_names: tuple[str, ...]


class RetrievalMetadata(DomainModel):
    """Retrieval provenance copied into the packet."""

    retrievers_used: tuple[str, ...]
    candidate_count: int
    retrieval_confidence: float


class SignalMetadata(DomainModel):
    """Signal-engine provenance copied into the packet."""

    algorithm_version: str
    signal_names: tuple[str, ...]
    explanation: str


class PipelineMetadata(DomainModel):
    """Versioned pipeline contract metadata."""

    pipeline_name: str = "cortex-notify"
    pipeline_version: str = "phase6.75-v1"
    stages: tuple[str, ...] = (
        "context",
        "personalization",
        "retrieval",
        "features",
        "signals",
        "packet",
    )


class ExecutionMetadata(DomainModel):
    """Packet creation execution metadata."""

    created_at: datetime
    duration_ms: float


class VersionMetadata(DomainModel):
    """Component versions participating in packet construction."""

    packet_version: str = "phase6.75-v1"
    feature_version: str = "phase6-v1"
    retrieval_version: str = "phase5-v1"
    signal_version: str = "phase6.5-v1"


class DecisionPacket(DomainModel):
    """Single immutable contract for a future Router Agent."""

    context: MessageContext
    personalization: PersonalizationProfile
    evidence: EvidenceBundle
    features: DecisionFeatures
    signals: DecisionSignals
    feature_metadata: FeatureMetadata
    retrieval_metadata: RetrievalMetadata
    signal_metadata: SignalMetadata
    pipeline_metadata: PipelineMetadata
    trace_metadata: TraceMetadata
    execution_metadata: ExecutionMetadata
    version_metadata: VersionMetadata
