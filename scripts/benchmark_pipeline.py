"""Benchmark the final end-to-end pipeline."""

import time

from app.services.container import build_container
from pipeline.service import ExecutionPipeline


def main() -> None:
    """Print end-to-end batch latency and throughput."""
    container = build_container()
    ids = tuple(message.message_id for message in container.message_repository.list())
    pipeline = ExecutionPipeline(container)
    started = time.perf_counter()
    pipeline.run(ids)
    elapsed = time.perf_counter() - started
    print(
        f"messages={len(ids)} seconds={elapsed:.3f} throughput_per_second={len(ids) / elapsed:.2f}"
    )
    print(pipeline.metrics.snapshot())


if __name__ == "__main__":
    main()
