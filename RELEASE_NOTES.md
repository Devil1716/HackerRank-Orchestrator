# Cortex Notify 1.0.0

This is the final frozen engineering release for HackerRank submission.

Highlights:

- End-to-end execution from `dataset/messages.csv` to `output.csv`.
- Exact HackerRank output schema.
- Deterministic preprocessing and immutable DecisionPacket handoff.
- Single isolated Router Agent with strict validation and repair.
- Reproducible local Mock provider, structured logs, metrics, and benchmarks.
- Docker and CLI support.

Known limitation: full-dataset gold labels and external provider credentials are not included, so provider and hidden-set accuracy rankings cannot be measured locally.
