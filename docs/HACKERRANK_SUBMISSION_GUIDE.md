# HackerRank Submission Guide

## Problem understanding

Cortex Notify classifies each WhatsApp notification as `notify`, `digest`, or
`mute`. The submission must preserve useful messages, reduce notification
fatigue, and remain deterministic and explainable under incomplete context.

## Execution path

```text
CSV repositories -> context -> personalization -> retrieval -> features
    -> priority/risk signals -> immutable DecisionPacket -> Router Agent
    -> validation/repair -> output.csv
```

The Router Agent sees one `DecisionPacket`; it never queries repositories or
reimplements feature calculations. The deterministic stages establish the
evidence and constraints before reasoning.

## Engineering decisions

- Polars lazy CSV access keeps dataset I/O isolated and predictable.
- Pydantic models make every boundary typed and immutable where the contract
  requires it.
- Feature and signal versions are carried with the packet for auditability.
- Strict output validation rejects invalid actions and unsupported evidence.
- The Mock provider is the offline, reproducible baseline; external providers
  are optional and are not required for the judge path.

## Why this scores well

The design combines lexical safety cues, user behavior, relationship history,
business trust, temporal context, and retrieved evidence before choosing an
action. This provides stable behavior when an LLM is unavailable and gives the
reasoner compact, high-signal inputs instead of a raw feature dump.

## Trade-offs and limitations

The current benchmark fixture is a smoke/evaluation set rather than the hidden
HackerRank gold set, so local accuracy is directional. External provider
comparisons remain unverified without credentials. Docker validation is
environment-dependent; the image build command is documented and should be
run on a host with Docker Desktop or a Linux daemon.

## Reproduce the submission

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m orchestrate health
.\.venv\Scripts\python.exe -m orchestrate run --output output.csv
```

The equivalent installed console command is `orchestrate run --output
output.csv`. See [README.md](../README.md) for configuration, tests, and
benchmark commands.

