# Phase 6.5 — Priority and Risk Engine

The Priority and Risk Engine consumes only immutable `DecisionFeatures` and
returns immutable `DecisionSignals`. It is a compact explainability boundary
before any future Router Agent. It does not access repositories, perform
retrieval, call an LLM, or inspect media.

Ten signals are generated: priority, urgency, risk, trust, spam, relationship,
business, context, engagement, and evidence. Each contains a normalized value,
confidence, source feature names, algorithm version, supporting evidence IDs, and
a human-readable reason. `RecommendationMetadata` records the complete signal
set and source feature count without making a notify/digest/mute decision.

Aggregation uses fixed weighted averages. Priority weights urgency, momentum,
business criticality, relationship, historical similarity, and evidence equally
within the documented weights in `priority/strategies.py`; each other signal has
an explicit named weight map. Missing features contribute no weight and produce
zero confidence when no source exists. The engine performs one feature-map build,
then one aggregation pass. All values are normalized to `[0, 1]` and validation
rejects missing provenance or out-of-range values.

Structured logs cover generation, aggregation, validation, and latency. The
algorithm version is `phase6.5-v1`. This phase ends before Router Agent work.
