"""Typed feature-engineering failures."""


class FeatureEngineeringError(Exception):
    """Base feature-engineering error."""


class FeatureInputError(FeatureEngineeringError):
    """Required feature inputs are malformed or inconsistent."""


class FeatureValidationError(FeatureEngineeringError):
    """A calculated feature violates the feature contract."""
