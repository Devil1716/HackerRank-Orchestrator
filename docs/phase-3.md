# Cortex Notify Phase 3 — Context Builder

## Architecture

The Context Builder is the only orchestration boundary between repositories
and downstream modules:

```text
Repositories -> ContextBuilderService -> immutable MessageContext -> downstream layers
```

`ContextBuilderService` depends only on `RepositorySet`, `Settings`, and a
structured logger. It performs no ranking, policy, scoring, personalization,
retrieval, AI, OCR, Whisper, or feature engineering.

## Context lifecycle

1. Resolve an incoming message object or message ID.
2. Resolve the required recipient and normalized conversation.
3. Resolve optional sender, business, group, media, and group membership data.
4. Resolve bounded conversation history, notification history, interaction
   history, and relevant business history.
5. Resolve known participant profiles.
6. Compute descriptive counts and timestamp metadata only.
7. Construct one frozen `MessageContext`.

Missing optional data is logged and represented as `None` or an empty tuple.
Missing required messages, recipients, or conversations raises a typed context
error.

## Repository interaction sequence

```text
message -> recipient -> conversation -> sender/business/group/media
         -> memberships/participants
         -> conversation/notification/interaction/business history
         -> descriptive statistics -> MessageContext
```

No downstream component receives repository references from the builder result.

## Observability

Structured events include context creation start, repository queries, optional
data misses, successful construction, and failures. Message contents and media
contents are never logged. Stage lifecycle logging records the overall builder
duration and status.

## Performance decisions

The builder makes one query per required resource and reuses repository caches.
History is bounded by `context_history_limit`. Participant IDs are
deduplicated before batch lookup. Descriptive statistics operate on already
loaded immutable tuples and do not create tabular copies.

## Error handling

Required resolution failures use `MessageNotFoundError`,
`RecipientNotFoundError`, or `ConversationNotFoundError`. Repository failures
are wrapped as `RepositoryQueryError`; unexpected assembly failures use
`ContextConstructionError`. Optional resources never cause a context build to
fail.

## Future extension strategy

Downstream phases should consume `MessageContext` and must not call
repositories. New context fields should be added as typed immutable models;
policy, ranking, evidence selection, and personalization belong outside this
orchestration service.

Phase 4, the Personalization & Evidence Layer, is explicitly not implemented.
