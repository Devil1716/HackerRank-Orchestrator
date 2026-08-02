"""Validation service contracts."""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class Validator(ABC):
    """Validate a typed object at an application boundary."""

    @abstractmethod
    def validate(self, value: T) -> T:
        """Return the validated value or raise an application error."""
        raise NotImplementedError
