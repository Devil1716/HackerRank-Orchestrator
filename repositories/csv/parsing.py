"""Safe scalar normalization from CSV strings to domain values."""

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from utils.repository_errors import MalformedRecordError, MalformedTimestampError


def text(row: dict[str, object], field: str, path: Path, row_number: int) -> str | None:
    """Return a trimmed nullable text value."""
    value = row.get(field)
    if value is None:
        return None
    return str(value).strip() or None


def required_text(row: dict[str, object], field: str, path: Path, row_number: int) -> str:
    """Return required text or a typed malformed-record error."""
    value = text(row, field, path, row_number)
    if value is None:
        raise MalformedRecordError(path, row_number, field, "value is required")
    return value


def integer(
    row: dict[str, object], field: str, path: Path, row_number: int, default: int = 0
) -> int:
    """Parse a non-negative integer field."""
    value = text(row, field, path, row_number)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise MalformedRecordError(path, row_number, field, "expected integer") from exc


def boolean(
    row: dict[str, object], field: str, path: Path, row_number: int, default: bool = False
) -> bool:
    """Parse common CSV boolean encodings."""
    value = text(row, field, path, row_number)
    if value is None:
        return default
    if value.lower() in {"1", "true", "yes"}:
        return True
    if value.lower() in {"0", "false", "no"}:
        return False
    raise MalformedRecordError(path, row_number, field, "expected boolean")


def timestamp(
    row: dict[str, object], field: str, path: Path, row_number: int, *, required: bool = True
) -> datetime | None:
    """Parse ISO-like timestamps, interpreting timezone-less CSV values as UTC."""
    value = text(row, field, path, row_number)
    if value is None:
        if required:
            raise MalformedTimestampError(path, row_number, field, "value is required")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MalformedTimestampError(path, row_number, field, "expected ISO timestamp") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def enum_value[EnumT: Enum](
    row: dict[str, object],
    field: str,
    enum_type: type[EnumT],
    path: Path,
    row_number: int,
) -> EnumT:
    """Parse a closed enum value and report invalid source data safely."""
    value = required_text(row, field, path, row_number)
    try:
        return enum_type(value)
    except ValueError as exc:
        raise MalformedRecordError(path, row_number, field, f"unsupported value {value!r}") from exc


def optional_enum[EnumT: Enum](
    row: dict[str, object],
    field: str,
    enum_type: type[EnumT],
    path: Path,
    row_number: int,
) -> EnumT | None:
    """Parse a nullable closed enum value."""
    value = text(row, field, path, row_number)
    if value is None:
        return None
    try:
        return enum_type(value)
    except ValueError as exc:
        raise MalformedRecordError(path, row_number, field, f"unsupported value {value!r}") from exc
