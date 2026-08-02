"""Media access boundary without decoding or content interpretation."""

from abc import ABC, abstractmethod

from app.models import Media


class MediaProvider(ABC):
    """Resolve a media reference to a validated media descriptor."""

    @abstractmethod
    def resolve(self, media_id: str) -> Media | None:
        """Return metadata only; extraction belongs to dedicated adapters."""
        raise NotImplementedError
