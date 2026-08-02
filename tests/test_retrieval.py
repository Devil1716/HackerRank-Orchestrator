"""Phase 5 retrieval tests."""

import pytest
from pydantic import ValidationError

from app.services.container import build_container
from retrieval import HashEmbeddingProvider, InMemoryVectorStore
from retrieval.errors import CorruptVectorError, EmptyIndexError


def test_three_retrievers_merge_and_provenance_are_immutable() -> None:
    """The DI retrieval service returns a traceable frozen bundle."""
    container = build_container()
    context = container.context_builder.build("msg_091")
    profile = container.personalization_service.build(context)
    bundle = container.retrieval_service.retrieve(context, profile)
    assert set(bundle.retrievers_used) == {"message", "behavior", "personalization"}
    assert bundle.retrieval_confidence >= 0
    with pytest.raises(ValidationError):
        bundle.retrieval_confidence = 0  # type: ignore[misc]


def test_hash_provider_and_vector_store_are_deterministic() -> None:
    """Portable test adapters provide stable vectors and scores."""
    provider = HashEmbeddingProvider()
    store = InMemoryVectorStore()
    vector = provider.embed(["same text"])[0]
    store.add(["one"], [vector])
    assert store.search(vector, 1)[0][0] == "one"


def test_empty_and_corrupt_indexes_fail_typed() -> None:
    """Vector failures never become silent empty evidence."""
    store = InMemoryVectorStore()
    with pytest.raises(EmptyIndexError):
        store.search((1.0,), 1)
    with pytest.raises(CorruptVectorError):
        store.add(["bad"], [(float("nan"),)])
