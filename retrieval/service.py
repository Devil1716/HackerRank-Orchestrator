"""Retrieval orchestration, merge, reranking, and deterministic confidence."""

from collections.abc import Sequence
from functools import lru_cache

import structlog

from app.models import Evidence, EvidenceBundle, MessageContext, PersonalizationProfile
from app.models.enums import EvidenceType
from retrieval.ports import Reranker, RetrievalCandidate, Retriever


class ConfidenceCalculator:
    """Calculate bounded confidence from transparent retrieval signals."""

    def calculate(self, items: Sequence[Evidence], retriever_count: int) -> float:
        if not items:
            return 0.0
        similarity = sum(item.relevance for item in items) / len(items)
        reranker = sum(item.reranker_score for item in items) / len(items)
        agreement = min(
            1.0, len({item.source_retriever for item in items}) / max(retriever_count, 1)
        )
        support = min(1.0, len(items) / 5.0)
        return round(0.40 * similarity + 0.25 * reranker + 0.20 * agreement + 0.15 * support, 6)


class EvidenceMerger:
    """Deduplicate candidates while preserving provenance."""

    def merge(
        self, results: Sequence[tuple[str, Sequence[RetrievalCandidate]]]
    ) -> tuple[Evidence, ...]:
        merged: dict[str, Evidence] = {}
        for retriever_name, candidates in results:
            for rank, candidate in enumerate(candidates):
                current = Evidence(
                    evidence_id=candidate.evidence_id,
                    evidence_type=(
                        EvidenceType.HISTORICAL_MESSAGE
                        if retriever_name == "message"
                        else (
                            EvidenceType.BEHAVIOR
                            if retriever_name == "behavior"
                            else EvidenceType.METADATA
                        )
                    ),
                    source_message_id=(
                        candidate.evidence_id if retriever_name == "message" else None
                    ),
                    summary=candidate.summary,
                    relevance=candidate.similarity,
                    confidence=candidate.similarity,
                    source_retriever=retriever_name,
                    rank=rank,
                    reranker_score=0.0,
                    reason_selected=candidate.reason,
                )
                prior = merged.get(candidate.evidence_id)
                if prior is None or current.relevance > prior.relevance:
                    merged[candidate.evidence_id] = current
        return tuple(sorted(merged.values(), key=lambda item: (-item.relevance, item.evidence_id)))


class RetrievalService:
    """Execute the complete retrieval pipeline from context and profile only."""

    def __init__(
        self,
        retrievers: Sequence[Retriever],
        reranker: Reranker,
        merger: EvidenceMerger,
        confidence: ConfidenceCalculator,
        logger: structlog.stdlib.BoundLogger,
    ) -> None:
        self._retrievers = tuple(retrievers)
        self._reranker = reranker
        self._merger = merger
        self._confidence = confidence
        self._logger = logger

    @lru_cache(maxsize=128)
    def _cached(
        self, message_id: str, context: MessageContext, profile: PersonalizationProfile, limit: int
    ) -> EvidenceBundle:
        results = tuple(
            (retriever.name, retriever.retrieve(context, profile, limit))
            for retriever in self._retrievers
        )
        merged = self._merger.merge(results)
        rerank_scores = (
            self._reranker.rerank(context.message.message_text, [item.summary for item in merged])
            if merged
            else ()
        )
        ranked = tuple(
            item.model_copy(update={"reranker_score": score})
            for item, score in zip(merged, rerank_scores, strict=True)
        )
        confidence = self._confidence.calculate(ranked, len(self._retrievers))
        bundle = EvidenceBundle(
            items=ranked,
            retrieval_confidence=confidence,
            evidence_message_ids=tuple(
                item.source_message_id for item in ranked if item.source_message_id
            ),
            retrievers_used=tuple(retriever.name for retriever in self._retrievers),
            candidate_count=sum(len(result) for _, result in results),
            metadata=(("cache", "miss"),),
        )
        self._logger.info(
            "retrieval_bundle_created", evidence_count=len(bundle.items), confidence=confidence
        )
        return bundle

    def retrieve(
        self, context: MessageContext, profile: PersonalizationProfile, limit: int = 10
    ) -> EvidenceBundle:
        """Retrieve and merge evidence for one immutable input pair."""
        return self._cached(str(context.message.message_id), context, profile, limit)
