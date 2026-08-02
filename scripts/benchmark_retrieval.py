"""Small Phase 5 latency benchmark; no dataset mutation or output generation."""

from time import perf_counter

from app.services.container import build_container


def main() -> None:
    """Measure end-to-end retrieval and cache latency."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    start = perf_counter()
    container.retrieval_service.retrieve(context, profile)
    first_ms = (perf_counter() - start) * 1000
    start = perf_counter()
    container.retrieval_service.retrieve(context, profile)
    cached_ms = (perf_counter() - start) * 1000
    print(f"retrieval_ms={first_ms:.3f} cache_hit_ms={cached_ms:.3f}")


if __name__ == "__main__":
    main()
