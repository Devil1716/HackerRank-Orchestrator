"""Validation result models."""

from app.models.base import DomainModel
from app.models.enums import ValidationStatus


class ValidationError(DomainModel):
    """Structured validation failure detail."""

    code: str
    message: str
    field: str | None = None


class ValidationResult(DomainModel):
    """Result of validating a typed boundary object."""

    status: ValidationStatus
    errors: tuple[ValidationError, ...] = ()
