"""Shared, policy-free constants for stable external contracts."""

PROJECT_NAME = "Cortex Notify"
PROJECT_VERSION = "0.1.0"
ENV_PREFIX = "ORCHESTRATE_"
HEALTHY = "ok"
DEGRADED = "degraded"
REQUIRED_OUTPUT_COLUMNS = (
    "message_id",
    "action",
    "message_type",
    "reason",
    "confidence",
    "evidence_message_ids",
)
