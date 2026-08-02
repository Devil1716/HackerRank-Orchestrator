# ADR-0002: Context-only personalization layer

## Status

Accepted for Phase 4.

## Decision

Personalization is a pure application boundary over immutable `MessageContext`.
The builder creates relationship, behavior, preference, business, topic,
interaction, and metadata-only evidence profiles using documented deterministic
rules. It is composed into DI without repositories.

## Consequences

The layer is reproducible and testable, and storage migration does not change its
API. It cannot infer facts absent from structured context and deliberately leaves
unsupported semantics for later phases. It does not retrieve evidence, inspect
media, classify messages, or choose notify/digest/mute.
