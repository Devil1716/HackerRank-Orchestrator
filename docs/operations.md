# Operations

Configuration is environment-driven with the `ORCHESTRATE_` prefix. Copy
`.env.example` to `.env` for local development; never commit `.env` or secrets.

The foundation can be checked with:

```text
uv run orchestrate health
docker compose run --rm router health
```

The health command is intentionally read-only. It reports whether configured
data and output directories exist and does not create or modify predictions.
