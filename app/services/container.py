"""Small manual dependency-injection composition root."""

from dataclasses import dataclass

import structlog

from app.config.settings import Settings
from app.monitoring.logging import configure_logging
from context.ports import ContextBuilder
from context.service import ContextBuilderService
from features.service import FeatureEngineeringService
from orchestration.service import DecisionOrchestrator
from personalization.base import PersonalizationService
from personalization.service import DeterministicPersonalizationService
from priority.engine import PriorityRiskEngine
from repositories.base import (
    BusinessHistoryRepository,
    BusinessRepository,
    GroupMembershipRepository,
    GroupRepository,
    MessageEventRepository,
    MessageHistoryRepository,
    MessageRepository,
    UserRepository,
)
from repositories.factory import RepositorySet, build_repositories
from retrieval import (
    BehaviorRetriever,
    ConfidenceCalculator,
    DeterministicReranker,
    EvidenceMerger,
    HashEmbeddingProvider,
    InMemoryVectorStore,
    MessageRetriever,
    PersonalizationRetriever,
    RetrievalService,
)
from router.agent import RouterAgent
from router.prompts import (
    ContextPromptBuilder,
    EvidencePromptBuilder,
    InstructionPromptBuilder,
    PromptAssembler,
    SignalPromptBuilder,
    SystemPromptBuilder,
)
from router.providers import ProviderFactory


@dataclass(frozen=True)
class Container:
    """Dependencies shared by entry points; no service locator is used."""

    settings: Settings
    logger: structlog.stdlib.BoundLogger
    repositories: RepositorySet
    context_builder: ContextBuilder
    personalization_service: PersonalizationService
    retrieval_service: RetrievalService
    feature_engineering_service: FeatureEngineeringService
    priority_risk_engine: PriorityRiskEngine
    decision_orchestrator: DecisionOrchestrator
    router_agent: RouterAgent

    @property
    def message_repository(self) -> MessageRepository:
        """Backward-compatible access to the message repository."""
        return self.repositories.messages

    @property
    def user_repository(self) -> UserRepository:
        """Backward-compatible access to the user repository."""
        return self.repositories.users

    @property
    def group_repository(self) -> GroupRepository:
        """Backward-compatible access to the group repository."""
        return self.repositories.groups

    @property
    def group_membership_repository(self) -> GroupMembershipRepository:
        """Access user-to-group membership records."""
        return self.repositories.group_memberships

    @property
    def business_repository(self) -> BusinessRepository:
        """Backward-compatible access to the business repository."""
        return self.repositories.businesses

    @property
    def history_repository(self) -> MessageHistoryRepository:
        """Backward-compatible access to historical messages."""
        return self.repositories.message_history

    @property
    def event_repository(self) -> MessageEventRepository:
        """Backward-compatible access to message events."""
        return self.repositories.message_events

    @property
    def business_history_repository(self) -> BusinessHistoryRepository:
        """Access business relationship history."""
        return self.repositories.business_history


def build_container(settings: Settings | None = None) -> Container:
    """Construct the application graph from explicit settings."""
    resolved = settings or Settings()
    configure_logging(resolved.log_level)
    repositories = build_repositories(resolved)
    logger = structlog.get_logger("orchestrate")
    return Container(
        settings=resolved,
        logger=logger,
        repositories=repositories,
        context_builder=ContextBuilderService(repositories, resolved, logger),
        personalization_service=DeterministicPersonalizationService(logger),
        retrieval_service=RetrievalService(
            retrievers=(
                MessageRetriever(HashEmbeddingProvider(), InMemoryVectorStore()),
                BehaviorRetriever(HashEmbeddingProvider(), InMemoryVectorStore()),
                PersonalizationRetriever(HashEmbeddingProvider(), InMemoryVectorStore()),
            ),
            reranker=DeterministicReranker(),
            merger=EvidenceMerger(),
            confidence=ConfidenceCalculator(),
            logger=logger,
        ),
        feature_engineering_service=FeatureEngineeringService(logger),
        priority_risk_engine=PriorityRiskEngine(logger),
        decision_orchestrator=DecisionOrchestrator(logger),
        router_agent=RouterAgent(
            provider=ProviderFactory.create("mock"),
            assembler=PromptAssembler(
                (
                    SystemPromptBuilder(),
                    ContextPromptBuilder(),
                    EvidencePromptBuilder(),
                    SignalPromptBuilder(),
                    InstructionPromptBuilder(),
                )
            ),
            logger=logger,
        ),
    )
