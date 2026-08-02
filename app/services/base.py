"""Base application service contract."""

from abc import ABC, abstractmethod


class ApplicationService[RequestT, ResponseT](ABC):
    """Coordinate ports without owning domain policy."""

    @abstractmethod
    def execute(self, request: RequestT) -> ResponseT:
        """Execute one application operation."""
        raise NotImplementedError
