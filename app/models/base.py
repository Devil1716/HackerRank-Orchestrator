"""Shared immutable Pydantic model configuration."""

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Immutable, strict, JSON-schema-capable domain model base."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )
