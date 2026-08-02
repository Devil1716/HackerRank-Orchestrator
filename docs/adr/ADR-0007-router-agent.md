# ADR-0007: Single Notification Router Agent

## Status

Accepted for Phase 7.

## Decision

Use one pluggable Router Agent over immutable `DecisionPacket` inputs. Structured
prompt components, provider adapters, strict parsing, one repair attempt, and
version metadata form the AI boundary.

## Rationale

One agent keeps responsibility narrow and avoids hidden multi-agent policy. The
Decision Packet makes all deterministic evidence explicit. Provider abstraction
supports deployment choice without provider logic leaking into orchestration.
Prompt versioning makes behavior auditable, while repair converts malformed model
output into an explicit bounded failure path rather than silently accepting it.
