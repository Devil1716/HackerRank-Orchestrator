"""Typed failures raised by the retrieval boundary."""


class RetrievalError(Exception):
    """Base retrieval failure."""


class MissingEmbeddingError(RetrievalError):
    """An embedding could not be generated or loaded."""


class CorruptVectorError(RetrievalError):
    """A vector has invalid shape or values."""


class EmptyIndexError(RetrievalError):
    """A vector index has no searchable entries."""


class VectorStoreError(RetrievalError):
    """The vector-store adapter failed."""


class RerankerError(RetrievalError):
    """The isolated reranker failed."""
