"""Pure deterministic profile and evidence builders."""

from collections import Counter
from datetime import datetime

import structlog

from app.models import (
    BehaviorProfile,
    BusinessTrustProfile,
    EvidenceDescriptor,
    EvidenceProfile,
    InteractionProfile,
    MessageContext,
    NotificationPreferences,
    PersonalizationProfile,
    RelationshipProfile,
    TopicProfile,
)
from app.models.enums import BusinessCategory, EvidenceType, RelationshipType


class ProfileValidators:
    """Validate immutable profile invariants at the application boundary."""

    @staticmethod
    def validate(profile: PersonalizationProfile) -> PersonalizationProfile:
        if profile.user_id != profile.preferences.user_id:
            raise ValueError("profile and preferences must identify the same user")
        if profile.behavior and profile.behavior.user_id != profile.user_id:
            raise ValueError("behavior profile user mismatch")
        return profile


class ProfileFactory:
    """Construct domain profile models without interpretation side effects."""

    @staticmethod
    def relationship(context: MessageContext) -> RelationshipProfile | None:
        sender = context.sender
        if sender is None:
            return None
        membership = next(
            (item for item in context.group_memberships if item.user_id == sender.user_id), None
        )
        relationship = RelationshipType.UNKNOWN
        source = "observed_sender"
        if membership and membership.role.lower() == "admin":
            relationship, source = RelationshipType.ADMIN, "group_membership"
        elif context.group and context.group.group_type.lower() == "family":
            relationship, source = RelationshipType.FAMILY, "group_metadata"
        elif membership:
            relationship, source = RelationshipType.MEMBER, "group_membership"
        return RelationshipProfile(
            user_id=context.recipient.user_id,
            contact_id=sender.user_id,
            relationship_type=relationship,
            strength=1.0 if relationship != RelationshipType.UNKNOWN else 0.0,
            source=source,
            evidence_count=len(context.conversation_history),
        )

    @staticmethod
    def behavior(context: MessageContext) -> BehaviorProfile:
        events = context.interaction_history
        sent = max(len(events), 1)
        opened = sum(event.message_opened for event in events)
        replied = sum(event.message_replied for event in events)
        dismissed = sum(event.notification_dismissed for event in events)
        reported = sum(event.message_reported for event in events)
        delays = [
            event.reaction_time_minutes
            for event in events
            if event.reaction_time_minutes is not None
        ]
        hours = tuple(sorted({item.created_at.hour for item in context.conversation_history}))
        engagement = (opened + replied) / (2 * sent)
        return BehaviorProfile(
            user_id=context.recipient.user_id,
            open_rate=opened / sent,
            reply_rate=replied / sent,
            dismissal_rate=dismissed / sent,
            report_rate=reported / sent,
            average_response_delay_minutes=sum(delays) / len(delays) if delays else None,
            engagement_frequency=engagement,
            active_hours=hours,
            communication_intensity=min(len(context.conversation_history) / 100.0, 1.0),
        )

    @staticmethod
    def preferences(context: MessageContext) -> NotificationPreferences:
        muted = tuple(
            sorted({item.business_id for item in context.business_history if item.opted_out})
        )
        return NotificationPreferences(
            user_id=context.recipient.user_id,
            do_not_disturb_window=context.recipient.do_not_disturb_window,
            muted_conversation_ids=(context.conversation.conversation_id,)
            if context.group_memberships
            and any(item.group_muted_by_user for item in context.group_memberships)
            else (),
            digest_enabled=True,
            preferred_conversation_types=(context.conversation.conversation_type.value,),
            muted_business_ids=muted,
        )

    @staticmethod
    def businesses(context: MessageContext) -> tuple[BusinessTrustProfile, ...]:
        records = list(context.business_history)
        if context.business and not any(
            item.business_id == context.business.business_id for item in records
        ):
            if context.business_history:
                records.append(
                    context.business_history[0].model_copy(
                        update={"business_id": context.business.business_id}
                    )
                )
        result = []
        for record in records:
            trust = min(
                1.0,
                (0.5 if record.opted_in else 0.0)
                + min(record.order_count / 10.0, 0.3)
                + min(record.messages_replied_30d / 10.0, 0.2),
            )
            result.append(
                BusinessTrustProfile(
                    user_id=context.recipient.user_id,
                    business_id=record.business_id,
                    category=context.business.category
                    if context.business
                    else BusinessCategory.UNKNOWN,
                    trust=trust,
                    has_recent_transaction=record.order_count > 0,
                    interaction_frequency=record.activity_count_180d,
                    recurring=record.order_count > 1,
                )
            )
        return tuple(sorted(result, key=lambda item: item.business_id))

    @staticmethod
    def topics(context: MessageContext) -> tuple[TopicProfile, ...]:
        vocabulary = {
            "meeting": ("meeting", "calendar", "schedule"),
            "delivery": ("delivery", "deliver", "order", "shipment"),
            "travel": ("flight", "hotel", "travel", "boarding"),
            "banking": ("bank", "payment", "account", "transaction"),
            "health": ("doctor", "health", "medicine", "appointment"),
            "work": ("work", "project", "office", "manager"),
            "family": ("family", "home", "birthday"),
        }
        occurrences: Counter[str] = Counter()
        latest: dict[str, datetime] = {}
        for item in (context.message, *context.conversation_history):
            text = item.message_text.lower()
            for topic, terms in vocabulary.items():
                if any(term in text for term in terms):
                    occurrences[topic] += 1
                    latest[topic] = max(latest.get(topic, item.created_at), item.created_at)
        total = max(sum(occurrences.values()), 1)
        return tuple(
            TopicProfile(
                user_id=context.recipient.user_id,
                topic_id=topic,
                affinity=count / total,
                occurrence_count=count,
                last_occurrence_at=latest[topic],
                recurring=count > 1,
            )
            for topic, count in sorted(occurrences.items())
        )

    @staticmethod
    def interaction(context: MessageContext) -> InteractionProfile:
        events = context.interaction_history
        timestamps = [item.created_at for item in events if item.created_at is not None]
        return InteractionProfile(
            user_id=context.recipient.user_id,
            conversation_message_count=len(context.conversation_history),
            interaction_count=len(events),
            opened_count=sum(item.message_opened for item in events),
            replied_count=sum(item.message_replied for item in events),
            dismissed_count=sum(item.notification_dismissed for item in events),
            reported_count=sum(item.message_reported for item in events),
            business_interaction_count=len(context.business_history),
            last_interaction_at=max(timestamps) if timestamps else None,
        )


class EvidenceProfileBuilder:
    """Prepare metadata-only evidence descriptors; never retrieves content."""

    def build(self, context: MessageContext) -> EvidenceProfile:
        descriptors = [
            EvidenceDescriptor(
                evidence_type=EvidenceType.HISTORICAL_MESSAGE,
                reference_ids=tuple(item.message_id for item in context.conversation_history),
                summary="conversation history metadata",
                time_start=min(
                    (item.created_at for item in context.conversation_history), default=None
                ),
                time_end=max(
                    (item.created_at for item in context.conversation_history), default=None
                ),
            ),
            EvidenceDescriptor(
                evidence_type=EvidenceType.INTERACTION,
                reference_ids=tuple(item.interaction_id for item in context.interaction_history),
                summary="interaction history metadata",
            ),
        ]
        if context.media:
            descriptors.append(
                EvidenceDescriptor(
                    evidence_type=EvidenceType.MEDIA,
                    reference_ids=(context.media.media_id,),
                    media_ids=(context.media.media_id,),
                    summary="media reference metadata; content not extracted",
                )
            )
        return EvidenceProfile(descriptors=tuple(descriptors))


class ProfileAggregationService:
    """Aggregate independently built profiles into one immutable result."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        self._logger = logger

    def build(self, context: MessageContext) -> PersonalizationProfile:
        relationship = ProfileFactory.relationship(context)
        businesses = ProfileFactory.businesses(context)
        self._logger.info(
            "relationship_extracted",
            user_id=str(context.recipient.user_id),
            relationship=str(relationship.relationship_type) if relationship else "none",
        )
        self._logger.info("preferences_extracted", user_id=str(context.recipient.user_id))
        topics = ProfileFactory.topics(context)
        self._logger.info(
            "topics_aggregated", user_id=str(context.recipient.user_id), topic_count=len(topics)
        )
        self._logger.info(
            "business_profiled",
            user_id=str(context.recipient.user_id),
            business_count=len(businesses),
        )
        profile = PersonalizationProfile(
            user_id=context.recipient.user_id,
            relationship=relationship,
            preferences=ProfileFactory.preferences(context),
            behavior=ProfileFactory.behavior(context),
            business_trust=businesses[0] if businesses else None,
            business_trust_profiles=businesses,
            topics=topics,
            interaction=ProfileFactory.interaction(context),
        )
        self._logger.info("personalization_profile_created", user_id=str(profile.user_id))
        return profile


class PersonalizationBuilder(ProfileAggregationService):
    """Top-level Phase 4 builder with evidence and validation."""

    def __init__(self, logger: structlog.stdlib.BoundLogger) -> None:
        super().__init__(logger)
        self._evidence = EvidenceProfileBuilder()

    def build(self, context: MessageContext) -> PersonalizationProfile:
        base = super().build(context)
        evidence = self._evidence.build(context)
        self._logger.info(
            "evidence_prepared",
            user_id=str(context.recipient.user_id),
            descriptor_count=len(evidence.descriptors),
        )
        result = base.model_copy(update={"evidence": evidence})
        validated = ProfileValidators.validate(result)
        self._logger.info("profile_validated", user_id=str(validated.user_id))
        self._logger.info("personalization_completed", user_id=str(validated.user_id))
        return validated
