"""Repository-specific failures with safe, actionable context."""

from pathlib import Path

from utils.errors import RepositoryError


class DatasetNotFoundError(RepositoryError):
    """Raised when a configured dataset file does not exist."""

    def __init__(self, path: Path) -> None:
        """Store the missing path for diagnostics."""
        super().__init__(f"dataset file not found: {path}")
        self.path = path


class InvalidSchemaError(RepositoryError):
    """Raised when a dataset is missing required columns."""

    def __init__(self, path: Path, missing: tuple[str, ...]) -> None:
        """Store the path and missing schema columns."""
        super().__init__(f"invalid schema for {path}; missing columns: {', '.join(missing)}")
        self.path = path
        self.missing = missing


class DuplicateRecordError(RepositoryError):
    """Raised when a primary-key column contains duplicate values."""

    def __init__(self, path: Path, key: str, value: str) -> None:
        """Store the duplicate key details."""
        super().__init__(f"duplicate {key}={value!r} in {path}")
        self.path = path
        self.key = key
        self.value = value


class MalformedRecordError(RepositoryError):
    """Raised when a row cannot become its typed domain model."""

    def __init__(self, path: Path, row_number: int, field: str, detail: str) -> None:
        """Store the malformed row location and safe detail."""
        super().__init__(f"malformed record in {path} row {row_number}, field {field}: {detail}")
        self.path = path
        self.row_number = row_number
        self.field = field
        self.detail = detail


class MalformedTimestampError(MalformedRecordError):
    """Raised when a timestamp cannot be parsed as an aware timestamp."""


class UnsupportedMediaReferenceError(RepositoryError):
    """Raised when a media record uses an unsupported media type."""


class EmptyDatasetError(RepositoryError):
    """Raised only by repositories configured to require at least one row."""
