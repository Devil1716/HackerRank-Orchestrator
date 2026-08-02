"""Versioned structured prompt components and budget management."""

import json

from app.models import DecisionPacket
from router.contracts import PromptComponent
from router.errors import PromptBudgetError


class PromptVersionManager:
    """Manage the stable Router prompt version."""

    version = "router-prompt-v1"


class PromptRegistry:
    """Registry of prompt template names and versions."""

    templates = {"system": PromptVersionManager.version}


class PromptTemplates:
    """Static prompt instructions; no raw repository data is accepted."""

    system = (
        "You are Cortex Notify's notification router. Decide notify, digest, or mute. "
        "Use only the supplied DecisionPacket. Do not invent facts. Return strict JSON "
        "with action, message_type, reason, confidence, and evidence_message_ids."
    )
    instruction = "Choose exactly one allowed action and express uncertainty through confidence."


class SystemPromptBuilder(PromptComponent):
    """Build mission, constraints, schema, and refusal instructions."""

    def build(self, packet: DecisionPacket) -> str:
        return PromptTemplates.system


class ContextPromptBuilder(PromptComponent):
    """Build a compact context section from packet metadata."""

    def build(self, packet: DecisionPacket) -> str:
        return json.dumps(
            {
                "message_id": packet.context.message.message_id,
                "conversation_type": packet.context.conversation.conversation_type.value,
                "message_text": packet.context.message.message_text[:1000],
            },
            sort_keys=True,
        )


class EvidencePromptBuilder(PromptComponent):
    """Build bounded evidence without exposing retrieval internals beyond evidence."""

    def build(self, packet: DecisionPacket) -> str:
        items = [
            {"id": item.evidence_id, "summary": item.summary[:300], "relevance": item.relevance}
            for item in packet.evidence.items[:10]
        ]
        return json.dumps(items, sort_keys=True)


class SignalPromptBuilder(PromptComponent):
    """Build compact high-level signals for reasoning."""

    def build(self, packet: DecisionPacket) -> str:
        signals = {
            name: {"value": signal.value, "confidence": signal.confidence}
            for name, signal in packet.signals
            if name != "recommendation"
        }
        return json.dumps(signals, sort_keys=True)


class InstructionPromptBuilder(PromptComponent):
    """Build final output instructions."""

    def build(self, packet: DecisionPacket) -> str:
        return PromptTemplates.instruction


class PromptAssembler:
    """Compose independent sections under a deterministic token budget."""

    def __init__(self, components: tuple[PromptComponent, ...], max_tokens: int = 4000) -> None:
        self._components = components
        self._max_tokens = max_tokens

    @staticmethod
    def estimate_tokens(prompt: str) -> int:
        return max(1, len(prompt) // 4)

    def assemble(self, packet: DecisionPacket) -> tuple[str, int]:
        sections = [component.build(packet) for component in self._components]
        prompt = "\n\n".join(sections)
        tokens = self.estimate_tokens(prompt)
        if tokens > self._max_tokens:
            prompt = prompt[: self._max_tokens * 4]
            tokens = self.estimate_tokens(prompt)
        if tokens > self._max_tokens:
            raise PromptBudgetError("assembled prompt exceeds token budget")
        return prompt, tokens
