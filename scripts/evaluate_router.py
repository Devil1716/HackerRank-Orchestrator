"""Evaluate local Router Agent latency and repair behavior."""

from time import perf_counter

from app.services.container import build_container


def main() -> None:
    """Run one mock-provider decision measurement."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    evidence = container.retrieval_service.retrieve(context, profile)
    features = container.feature_engineering_service.build(context, profile, evidence)
    signals = container.priority_risk_engine.build(features)
    packet = container.decision_orchestrator.build(context, profile, evidence, features, signals)
    started = perf_counter()
    decision = container.router_agent.decide(packet)
    print(
        f"provider={decision.provider} latency_ms={decision.latency_ms:.3f} "
        f"tokens={decision.token_usage}"
    )
    print(f"wall_ms={(perf_counter() - started) * 1000:.3f} repairs={decision.repair_count}")


if __name__ == "__main__":
    main()
