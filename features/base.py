"""Feature extraction boundary with no feature policy in Phase 0."""

from abc import ABC, abstractmethod

from app.models import Context

type FeatureVector = dict[str, float | int | str | bool | None]


class FeatureExtractor(ABC):
    """Derive a serializable feature vector from structured context."""

    @abstractmethod
    def extract(self, context: Context) -> FeatureVector:
        """Return deterministic features."""
        raise NotImplementedError
