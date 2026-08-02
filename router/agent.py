"""Notification Router Agent orchestration."""

from time import perf_counter

import structlog

from app.models import Decision, DecisionPacket
from router.contracts import Provider
from router.prompts import PromptAssembler
from router.validation import DecisionParser, RepairEngine, RetryPolicy, SchemaValidator


class RouterAgent:
    """The only AI boundary: reason over a DecisionPacket and return Decision."""

    def __init__(
        self, provider: Provider, assembler: PromptAssembler, logger: structlog.stdlib.BoundLogger
    ) -> None:
        self._provider = provider
        self._assembler = assembler
        self._parser = DecisionParser()
        self._validator = SchemaValidator()
        self._repair = RepairEngine()
        self._logger = logger

    def decide(self, packet: DecisionPacket) -> Decision:
        """Generate, validate, repair once if needed, and return a decision."""
        started = perf_counter()
        prompt, _ = self._assembler.assemble(packet)
        self._logger.info("router_provider_selected", provider=self._provider.name)
        response = self._provider.complete(prompt)
        repairs = 0
        try:
            decision = self._parser.parse(
                response.content, packet, response.provider, response.token_usage, 0.0, repairs
            )
        except Exception:
            if repairs >= RetryPolicy.max_repairs:
                raise
            repairs += 1
            self._logger.info("router_output_repair", repair_count=repairs)
            response = self._repair.repair(self._provider, response.content)
            decision = self._parser.parse(
                response.content, packet, response.provider, response.token_usage, 0.0, repairs
            )
        latency = round((perf_counter() - started) * 1000, 3)
        final = decision.model_copy(update={"latency_ms": latency, "repair_count": repairs})
        validated = self._validator.validate(final)
        self._logger.info(
            "router_decision_generated", provider=validated.provider, latency_ms=latency
        )
        return validated
