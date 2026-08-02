"""Phase 7 Router Agent tests."""

import json

from app.services.container import build_container
from router.agent import RouterAgent
from router.prompts import PromptAssembler, SystemPromptBuilder
from router.providers import CallableProvider


def _packet() -> object:
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    evidence = container.retrieval_service.retrieve(context, profile)
    features = container.feature_engineering_service.build(context, profile, evidence)
    signals = container.priority_risk_engine.build(features)
    return container.decision_orchestrator.build(context, profile, evidence, features, signals)


def test_mock_router_returns_strict_decision() -> None:
    """The Router Agent consumes a packet and returns immutable structured output."""
    container = build_container()
    decision = container.router_agent.decide(_packet())
    assert decision.provider == "mock"
    assert decision.decision_version == "phase7-v1"


def test_invalid_json_is_repaired_once() -> None:
    """Malformed first output follows the bounded repair path."""
    responses = iter(
        [
            "not-json",
            json.dumps(
                {
                    "action": "mute",
                    "message_type": "spam",
                    "reason": "repaired",
                    "confidence": 0.8,
                    "evidence_message_ids": [],
                }
            ),
        ]
    )
    agent = RouterAgent(
        CallableProvider("test", lambda prompt: next(responses)),
        PromptAssembler((SystemPromptBuilder(),)),
        build_container().logger,
    )
    decision = agent.decide(_packet())
    assert decision.repair_count == 1
