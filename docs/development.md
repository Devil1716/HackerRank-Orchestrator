# Development workflow

```text
uv sync --extra dev
uv run pre-commit install
uv run orchestrate health
make check
```

The quality gate is Ruff, Black, mypy, and pytest. Python 3.12 is the declared
runtime. The current machine may use a newer interpreter for local checks, but
CI and Docker target Python 3.12.
