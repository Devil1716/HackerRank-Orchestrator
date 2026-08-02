"""Measure Phase 6 feature-engineering latency."""

import tracemalloc
from time import perf_counter

from app.services.container import build_container


def main() -> None:
    """Print cold and warm feature pipeline latency."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    evidence = container.retrieval_service.retrieve(context, profile)
    started = perf_counter()
    tracemalloc.start()
    container.feature_engineering_service.build(context, profile, evidence)
    cold_ms = (perf_counter() - started) * 1000
    _, peak_bytes = tracemalloc.get_traced_memory()
    allocation_count = len(tracemalloc.take_snapshot().statistics("lineno"))
    tracemalloc.stop()
    started = perf_counter()
    container.feature_engineering_service.build(context, profile, evidence)
    warm_ms = (perf_counter() - started) * 1000
    print(
        f"feature_cold_ms={cold_ms:.3f} feature_warm_ms={warm_ms:.3f} "
        f"peak_bytes={peak_bytes} allocation_sites={allocation_count}"
    )


if __name__ == "__main__":
    main()
