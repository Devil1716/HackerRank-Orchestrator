"""Metrics and lightweight execution profiling."""

import tracemalloc
from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class MetricsCollector:
    """Collect process-level counters and stage timings."""

    messages: int = 0
    validation_failures: int = 0
    repairs: int = 0
    token_usage: int = 0
    estimated_cost: float = 0.0
    latencies_ms: list[float] = field(default_factory=list)
    stage_latencies_ms: dict[str, list[float]] = field(default_factory=dict)
    peak_memory_bytes: int = 0

    def record_stage(self, stage: str, duration_ms: float) -> None:
        """Record one stage duration."""
        self.stage_latencies_ms.setdefault(stage, []).append(duration_ms)

    def snapshot(self) -> dict[str, object]:
        """Return JSON-compatible aggregate metrics."""
        return {
            "messages": self.messages,
            "validation_failures": self.validation_failures,
            "repairs": self.repairs,
            "token_usage": self.token_usage,
            "estimated_cost": self.estimated_cost,
            "average_latency_ms": sum(self.latencies_ms) / len(self.latencies_ms)
            if self.latencies_ms
            else 0.0,
            "stage_latencies_ms": {
                name: sum(values) / len(values) for name, values in self.stage_latencies_ms.items()
            },
            "peak_memory_bytes": self.peak_memory_bytes,
        }


class PipelineProfiler:
    """Measure one named stage."""

    def __init__(self, metrics: MetricsCollector, stage: str) -> None:
        self._metrics = metrics
        self._stage = stage
        self._started = 0.0

    def __enter__(self) -> "PipelineProfiler":
        self._started = perf_counter()
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self._metrics.record_stage(self._stage, (perf_counter() - self._started) * 1000)
        _, peak = tracemalloc.get_traced_memory()
        self._metrics.peak_memory_bytes = max(self._metrics.peak_memory_bytes, peak)
