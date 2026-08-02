"""OCR interface isolated behind a replaceable provider."""

from abc import ABC, abstractmethod

from app.models import Media


class OcrProvider(ABC):
    """Extract text from image media in a future phase."""

    @abstractmethod
    def extract_text(self, media: Media) -> str:
        """Return extracted text or raise a provider error."""
        raise NotImplementedError
