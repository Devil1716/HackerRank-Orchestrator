"""Tests proving Phase 0 interfaces remain abstract and policy-free."""

from inspect import isabstract

from features.base import FeatureExtractor
from ocr.base import OcrProvider
from reasoning.base import ReasoningService
from repositories.base import MessageRepository
from speech.base import SpeechProvider


def test_core_boundaries_are_abstract() -> None:
    """Prevent accidental concrete business implementations in Phase 0."""
    assert isabstract(MessageRepository)
    assert isabstract(FeatureExtractor)
    assert isabstract(ReasoningService)
    assert isabstract(OcrProvider)
    assert isabstract(SpeechProvider)
