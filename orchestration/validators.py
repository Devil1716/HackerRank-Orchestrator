"""Decision packet completeness validation."""

from app.models import DecisionPacket
from orchestration.errors import DecisionPacketValidationError


class DecisionPacketValidator:
    """Validate required sections and trace integrity."""

    @staticmethod
    def validate(packet: DecisionPacket) -> DecisionPacket:
        required = (
            packet.context,
            packet.personalization,
            packet.evidence,
            packet.features,
            packet.signals,
            packet.feature_metadata,
            packet.retrieval_metadata,
            packet.signal_metadata,
            packet.pipeline_metadata,
            packet.trace_metadata,
            packet.execution_metadata,
            packet.version_metadata,
        )
        if any(section is None for section in required):
            raise DecisionPacketValidationError("decision packet contains a missing section")
        if not packet.trace_metadata.stages:
            raise DecisionPacketValidationError("decision packet trace is empty")
        return packet
