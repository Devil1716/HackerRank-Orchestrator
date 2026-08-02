"""Small time utilities kept independent of business policy."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return an aware UTC timestamp suitable for logs and events."""
    return datetime.now(UTC)
