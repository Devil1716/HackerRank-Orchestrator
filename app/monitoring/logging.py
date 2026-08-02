"""Structured JSON logging setup and stage lifecycle helpers."""

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure one JSON renderer for standard and structured loggers."""
    logging.basicConfig(format="%(message)s", level=getattr(logging, level, logging.INFO))
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level, logging.INFO)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@contextmanager
def stage_log(logger: Any, *, message_id: str, stage: str) -> Iterator[None]:
    """Emit the required lifecycle fields for a stage, including failures."""
    started = time.perf_counter()
    try:
        yield
    except Exception as error:
        logger.error(
            "pipeline_stage",
            message_id=message_id,
            stage=stage,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
            status="error",
            errors=[str(error)],
        )
        raise
    else:
        logger.info(
            "pipeline_stage",
            message_id=message_id,
            stage=stage,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
            status="ok",
            errors=[],
        )
