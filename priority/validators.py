"""Decision signal validation."""

from app.models import DecisionSignals
from priority.errors import SignalValidationError


class SignalValidators:
    """Validate all signal ranges and provenance invariants."""

    @staticmethod
    def validate(signals: DecisionSignals) -> DecisionSignals:
        for name, signal in signals.model_dump().items():
            if name == "recommendation":
                continue
            if not 0.0 <= signal["value"] <= 1.0 or not 0.0 <= signal["confidence"] <= 1.0:
                raise SignalValidationError(f"{name} is outside normalized range")
            if not signal["features_used"]:
                raise SignalValidationError(f"{name} has no feature provenance")
        return signals
