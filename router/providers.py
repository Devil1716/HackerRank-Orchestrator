"""Provider adapters and factory."""

import json
from collections.abc import Callable

from router.contracts import Provider, ProviderResponse
from router.errors import ProviderError


class MockProvider(Provider):
    """Deterministic competition baseline provider for tests and local runs."""

    name = "mock"

    def __init__(self, response: str | None = None) -> None:
        self.response = response if response is not None else ""

    def complete(self, prompt: str) -> ProviderResponse:
        if self.response != "":
            return ProviderResponse(
                self.response, token_usage=max(1, len(prompt) // 4), provider=self.name
            )
        text = prompt.lower()
        risk_terms = (
            "otp",
            "password",
            "prize",
            "lottery",
            "urgent payment",
            "click here",
            "verify account",
        )
        promotion_terms = ("sale", "discount", "offer", "promotion", "cashback", "limited time")
        event_terms = (
            "meeting",
            "schedule",
            "bus",
            "event",
            "appointment",
            "deadline",
            "today",
            "tomorrow",
        )
        payment_terms = ("payment", "invoice", "bill", "transaction", "due")
        if any(term in text for term in risk_terms):
            action, message_type, reason, confidence = (
                "mute",
                "scam",
                "Suspicious or unsafe language was detected.",
                0.92,
            )
        elif any(term in text for term in promotion_terms):
            action, message_type, reason, confidence = (
                "digest",
                "promotion",
                "Promotional content can wait for a digest.",
                0.78,
            )
        elif any(term in text for term in payment_terms):
            action, message_type, reason, confidence = (
                "notify",
                "payment",
                "A payment-related update may require timely attention.",
                0.84,
            )
        elif any(term in text for term in event_terms):
            action, message_type, reason, confidence = (
                "notify",
                "event",
                "A time-sensitive event or schedule update may require attention.",
                0.83,
            )
        else:
            action, message_type, reason, confidence = (
                "digest",
                "unknown",
                "The message is useful but lacks a strong interruption signal.",
                0.61,
            )
        return ProviderResponse(
            json.dumps(
                {
                    "action": action,
                    "message_type": message_type,
                    "reason": reason,
                    "confidence": confidence,
                    "evidence_message_ids": [],
                }
            ),
            token_usage=max(1, len(prompt) // 4),
            provider=self.name,
        )


class CallableProvider(Provider):
    """Adapter for an injected provider callback."""

    def __init__(self, name: str, callback: Callable[[str], str]) -> None:
        self.name = name
        self._callback = callback

    def complete(self, prompt: str) -> ProviderResponse:
        try:
            return ProviderResponse(self._callback(prompt), max(1, len(prompt) // 4), self.name)
        except Exception as error:
            raise ProviderError(f"provider {self.name} failed") from error


class OpenAIProvider(CallableProvider):
    """OpenAI adapter seam; transport is injected by the application."""

    def __init__(self, callback: Callable[[str], str]) -> None:
        super().__init__("openai", callback)


class GeminiProvider(CallableProvider):
    """Gemini adapter seam; transport is injected by the application."""

    def __init__(self, callback: Callable[[str], str]) -> None:
        super().__init__("gemini", callback)


class OllamaProvider(CallableProvider):
    """Ollama adapter seam; transport is injected by the application."""

    def __init__(self, callback: Callable[[str], str]) -> None:
        super().__init__("ollama", callback)


class VLLMProvider(CallableProvider):
    """vLLM adapter seam; transport is injected by the application."""

    def __init__(self, callback: Callable[[str], str]) -> None:
        super().__init__("vllm", callback)


class ProviderFactory:
    """Create adapters without leaking provider-specific logic to the agent."""

    @staticmethod
    def create(name: str = "mock") -> Provider:
        if name == "mock":
            return MockProvider()
        raise ProviderError(f"provider adapter is not configured: {name}")
