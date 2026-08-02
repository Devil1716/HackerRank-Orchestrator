.PHONY: install format lint typecheck test check health

install:
	uv sync --extra dev

hooks:
	uv run pre-commit install

format:
	uv run ruff format .
	uv run black app tests

lint:
	uv run ruff check .

typecheck:
	uv run mypy app api config context features media models orchestration ocr personalization pipeline priority reasoning repositories retrieval router speech utils validation

test:
	uv run pytest

check: lint typecheck test

health:
	uv run orchestrate health
