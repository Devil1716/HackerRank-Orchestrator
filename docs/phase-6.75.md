# Phase 6.75 — Decision Packet Orchestration

The Decision Orchestrator assembles the five deterministic outputs—
`MessageContext`, `PersonalizationProfile`, `EvidenceBundle`, `DecisionFeatures`,
and `DecisionSignals`—into one immutable `DecisionPacket`. A future Router Agent
will consume this packet as its only input. This phase makes no action decision.

The packet includes copied feature, retrieval, signal, pipeline, execution, and
version metadata. `TraceBuilder` records context, personalization, retrieval,
features, and signals stages with component, timestamps, duration, inputs,
outputs, warnings, and errors. `DecisionPacketValidator` rejects missing sections
and empty traces. Optional data inside `MessageContext` remains valid for partial
contexts; the five top-level inputs are required.

The packet is frozen Pydantic data, so downstream components cannot mutate the
orchestration result. This creates a stable handoff contract, keeps boundaries
auditable, and avoids giving reasoning hidden access to repositories or retrieval.
Router Agent, LLM, OCR, Whisper, and Phase 7 remain out of scope.
