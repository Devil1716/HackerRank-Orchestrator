# ADR-0006: Immutable Decision Packet

## Status

Accepted for Phase 6.75.

## Decision

Use one immutable `DecisionPacket` as the handoff between deterministic pipeline
stages and a future Router Agent. Include all five outputs plus structured
metadata and an execution trace.

## Rationale

A single packet prevents implicit cross-stage dependencies and makes the exact
inputs to reasoning inspectable. Immutable orchestration avoids later mutation of
evidence or signals, while trace and version metadata support reproducibility and
diagnosis. The packet itself does not perform reasoning or choose an action.
