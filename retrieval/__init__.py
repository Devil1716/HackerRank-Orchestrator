"""Evidence retrieval service interfaces."""

"""Phase 5 retrieval engine public API."""

from retrieval.ports import EmbeddingProvider, Reranker, Retriever, VectorStore
from retrieval.providers import BGEEmbeddingProvider, HashEmbeddingProvider
from retrieval.reranking import BGEReranker, DeterministicReranker
from retrieval.retrievers import BehaviorRetriever, MessageRetriever, PersonalizationRetriever
from retrieval.service import ConfidenceCalculator, EvidenceMerger, RetrievalService
from retrieval.store import FaissVectorStore, InMemoryVectorStore

__all__ = [
    "BGEEmbeddingProvider",
    "BGEReranker",
    "BehaviorRetriever",
    "ConfidenceCalculator",
    "DeterministicReranker",
    "EmbeddingProvider",
    "EvidenceMerger",
    "FaissVectorStore",
    "HashEmbeddingProvider",
    "InMemoryVectorStore",
    "MessageRetriever",
    "PersonalizationRetriever",
    "Reranker",
    "RetrievalService",
    "Retriever",
    "VectorStore",
]
