"""Independent context-only retrievers."""

from collections.abc import Sequence

from app.models import MessageContext, PersonalizationProfile
from retrieval.ports import EmbeddingProvider, RetrievalCandidate, Retriever, VectorStore


class _ContextRetriever(Retriever):
    """Shared lazy indexing mechanics for context-local candidates."""

    def __init__(self, embedding_provider: EmbeddingProvider, store: VectorStore) -> None:
        self._embedding_provider = embedding_provider
        self._store = store
        self._indexed = False

    def _search(
        self, query: str, candidates: Sequence[RetrievalCandidate], limit: int
    ) -> tuple[RetrievalCandidate, ...]:
        if not candidates:
            return ()
        vectors = self._embedding_provider.embed([candidate.summary for candidate in candidates])
        self._store.add([candidate.evidence_id for candidate in candidates], vectors)
        query_vector = self._embedding_provider.embed([query])[0]
        scores = dict(self._store.search(query_vector, limit))
        return tuple(
            sorted(
                (
                    candidate.__class__(
                        candidate.evidence_id,
                        candidate.summary,
                        scores[candidate.evidence_id],
                        candidate.reason,
                    )
                    for candidate in candidates
                    if candidate.evidence_id in scores
                ),
                key=lambda item: (-item.similarity, item.evidence_id),
            )[:limit]
        )


class MessageRetriever(_ContextRetriever):
    """Retrieve historical messages using semantic and metadata-local signals."""

    name = "message"

    def retrieve(
        self, context: MessageContext, profile: PersonalizationProfile, limit: int
    ) -> tuple[RetrievalCandidate, ...]:
        candidates = tuple(
            RetrievalCandidate(
                item.message_id,
                item.message_text,
                0.0,
                "conversation continuity; sender/business/group metadata retained",
            )
            for item in context.conversation_history
            if item.message_id != context.message.message_id
        )
        return self._search(context.message.message_text, candidates, limit)


class BehaviorRetriever(_ContextRetriever):
    """Retrieve interaction records with similar observed behavior."""

    name = "behavior"

    def retrieve(
        self, context: MessageContext, profile: PersonalizationProfile, limit: int
    ) -> tuple[RetrievalCandidate, ...]:
        candidates = tuple(
            RetrievalCandidate(
                event.interaction_id,
                f"opened={event.message_opened} replied={event.message_replied} "
                f"dismissed={event.notification_dismissed} latency={event.reaction_time_minutes}",
                0.0,
                "interaction frequency and response behavior",
            )
            for event in context.interaction_history
        )
        query = f"opened={profile.behavior.open_rate if profile.behavior else 0} replied={profile.behavior.reply_rate if profile.behavior else 0}"
        return self._search(query, candidates, limit)


class PersonalizationRetriever(_ContextRetriever):
    """Retrieve structured profile signals without reading repositories."""

    name = "personalization"

    def retrieve(
        self, context: MessageContext, profile: PersonalizationProfile, limit: int
    ) -> tuple[RetrievalCandidate, ...]:
        candidates = []
        if profile.relationship:
            candidates.append(
                RetrievalCandidate(
                    "relationship", str(profile.relationship), 0.0, "relationship profile"
                )
            )
        candidates.extend(
            RetrievalCandidate(
                f"topic:{topic.topic_id}",
                f"topic {topic.topic_id} occurrences {topic.occurrence_count}",
                0.0,
                "topic history",
            )
            for topic in profile.topics
        )
        candidates.extend(
            RetrievalCandidate(
                f"business:{business.business_id}",
                f"business {business.business_id} trust {business.trust}",
                0.0,
                "trusted business profile",
            )
            for business in profile.business_trust_profiles
        )
        return self._search(context.message.message_text, tuple(candidates), limit)
