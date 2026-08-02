# Performance Report

The final pipeline is batch-capable and instrumented for stage latency, tokens, repairs, cost, and peak memory. Run `scripts/benchmark_pipeline.py` for local measurements.
# Performance Report

Measured on the checked-in 110-message fixture with the deterministic Mock
router on Python 3.12.

| Metric | Measured value |
|---|---:|
| Messages | 110 |
| Throughput | 42.54 messages/s |
| Wall time | 2.586 s |
| Validation failures | 0 |
| Repairs | 0 |
| Average router latency | 0.487 ms |
| Average pipeline stage latency | 23.425 ms |
| Peak traced memory | 8.03 MB |
| Estimated provider cost | 0 |

The measurement is a local baseline, not a claim about the hidden judge
environment. Repeat it with `orchestrate benchmark` after installing the
locked dependencies. External-provider latency and cost are intentionally not
fabricated when credentials are unavailable.
