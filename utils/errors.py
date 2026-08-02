"""Stable application error hierarchy for all adapters and services."""


class CortexNotifyError(Exception):
    """Base class for expected application failures."""


class ConfigurationError(CortexNotifyError):
    """Raised when runtime configuration is invalid or incomplete."""


class RepositoryError(CortexNotifyError):
    """Raised when a repository cannot read or persist its contract."""


class ServiceError(CortexNotifyError):
    """Raised when an application service cannot complete its operation."""


class ValidationError(CortexNotifyError):
    """Raised when an input or output violates an application contract."""


class DependencyError(CortexNotifyError):
    """Raised when the composition root cannot construct a dependency."""
