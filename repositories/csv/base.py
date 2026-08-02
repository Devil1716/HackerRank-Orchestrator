"""Shared lazy Polars CSV mechanics for concrete repositories."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path

import polars as pl
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from utils.errors import RepositoryError
from utils.repository_errors import (
    DatasetNotFoundError,
    DuplicateRecordError,
    InvalidSchemaError,
    MalformedRecordError,
)


class CsvTable:
    """Lazy, schema-checked access to one CSV file."""

    def __init__(self, path: Path, required_columns: Sequence[str]) -> None:
        """Configure a lazy scan without touching the filesystem."""
        self.path = path
        self.required_columns = tuple(required_columns)
        self._lazy_frame: pl.LazyFrame | None = None
        self._rows: tuple[dict[str, object], ...] | None = None

    @property
    def is_loaded(self) -> bool:
        """Return whether this table has been collected into memory."""
        return self._rows is not None

    def lazy_frame(self) -> pl.LazyFrame:
        """Create and schema-check a lazy scan exactly once."""
        if self._lazy_frame is not None:
            return self._lazy_frame
        if not self.path.is_file():
            raise DatasetNotFoundError(self.path)
        try:
            frame = pl.scan_csv(self.path, infer_schema=False, null_values=[""])
            columns = tuple(frame.collect_schema().names())
        except Exception as exc:
            raise InvalidSchemaError(self.path, tuple(self.required_columns)) from exc
        missing = tuple(column for column in self.required_columns if column not in columns)
        if missing:
            raise InvalidSchemaError(self.path, missing)
        self._lazy_frame = frame
        return frame

    def rows(self) -> tuple[dict[str, object], ...]:
        """Collect rows once, keeping the Polars object private."""
        if self._rows is None:
            try:
                self._rows = tuple(self.lazy_frame().collect().to_dicts())
            except RepositoryError:
                raise
            except Exception as exc:
                raise InvalidSchemaError(self.path, tuple(self.required_columns)) from exc
        return self._rows


class CsvRepository[ModelT: BaseModel](ABC):
    """Typed repository base with lazy loading and primary-key caching."""

    def __init__(self, table: CsvTable, key_fn: Callable[[ModelT], str]) -> None:
        """Configure the table and primary-key projection."""
        self.table = table
        self._key_fn = key_fn
        self._items_cache: tuple[ModelT, ...] | None = None
        self._index_cache: dict[str, ModelT] | None = None

    @property
    def is_loaded(self) -> bool:
        """Return whether model conversion has happened."""
        return self._items_cache is not None

    def _items(self) -> tuple[ModelT, ...]:
        """Convert and validate rows once, then build a primary-key index."""
        if self._items_cache is not None:
            return self._items_cache
        converted: list[ModelT] = []
        index: dict[str, ModelT] = {}
        for row_number, row in enumerate(self.table.rows(), start=2):
            try:
                item = self._parse_row(row, row_number)
            except PydanticValidationError as exc:
                raise MalformedRecordError(self.table.path, row_number, "record", str(exc)) from exc
            key = self._key_fn(item)
            if key in index:
                raise DuplicateRecordError(self.table.path, "primary key", key)
            converted.append(item)
            index[key] = item
        self._items_cache = tuple(converted)
        self._index_cache = index
        return self._items_cache

    def get(self, record_id: str) -> ModelT | None:
        """Return a cached record by primary key."""
        self._items()
        assert self._index_cache is not None
        return self._index_cache.get(record_id)

    def get_many(self, record_ids: Sequence[str]) -> tuple[ModelT, ...]:
        """Return records in caller-provided order, omitting missing IDs."""
        return tuple(item for record_id in record_ids if (item := self.get(record_id)) is not None)

    def list(self) -> tuple[ModelT, ...]:
        """Return all records as an immutable tuple."""
        return self._items()

    def exists(self, record_id: str) -> bool:
        """Return whether the primary key exists."""
        return self.get(record_id) is not None

    @abstractmethod
    def _parse_row(self, row: dict[str, object], row_number: int) -> ModelT:
        """Map one private Polars row to a domain model."""
        raise NotImplementedError
