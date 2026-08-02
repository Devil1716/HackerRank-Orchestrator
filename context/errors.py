"""Context-builder-specific failures."""

from utils.errors import CortexNotifyError


class ContextBuilderError(CortexNotifyError):
    """Base class for expected context construction failures."""


class MessageNotFoundError(ContextBuilderError):
    """Raised when the requested incoming message does not exist."""


class RecipientNotFoundError(ContextBuilderError):
    """Raised when a required recipient user cannot be resolved."""


class ConversationNotFoundError(ContextBuilderError):
    """Raised when the message's required conversation cannot be resolved."""


class RepositoryQueryError(ContextBuilderError):
    """Raised when a repository fails during context construction."""


class ContextConstructionError(ContextBuilderError):
    """Raised for unexpected context assembly failures."""
