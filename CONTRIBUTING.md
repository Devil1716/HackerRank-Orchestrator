# Contributing

## Development setup

```text
uv sync --extra dev
uv run orchestrate health
uv run pytest
```

Use small, single-purpose modules. Domain models must not depend on adapters;
implementations depend on the interfaces in `app/core` and `app/repositories`.
Do not add secrets, organizer-only data, or generated predictions to git.

Before opening a change, run `make check` and document any intentionally
unimplemented adapter in `docs/architecture.md`.
