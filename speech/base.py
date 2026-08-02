"""Speech-to-text interface isolated behind a replaceable provider."""

from abc import ABC, abstractmethod

from app.models import Media


class SpeechProvider(ABC):
    """Transcribe voice media in a future phase."""

    @abstractmethod
    def transcribe(self, media: Media) -> str:
        """Return a transcript or raise a provider error."""
        raise NotImplementedError
