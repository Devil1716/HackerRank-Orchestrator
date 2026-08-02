# Cortex Notify Phase 1 — Domain Language

## Scope

Phase 1 defines only the immutable domain contract. It does not parse CSV,
retrieve evidence, calculate features, call an LLM, run OCR/Whisper, or make
notification decisions. Those concerns remain behind the Phase 0 boundaries.

## Model hierarchy

```text
DomainModel
├── Core: Message, User, Business, Group, Media, Conversation
│   └── NotificationHistory, InteractionHistory, BusinessHistory
├── Context: MessageContext, UserContext, BusinessContext, GroupContext
│   └── MediaContext, NotificationContext
├── Retrieval: Evidence, EvidenceBundle, RetrievedMessage
│   └── RetrievedBehavior, RetrievedPreference
├── Personalization: RelationshipProfile, NotificationPreferences
│   └── BehaviorProfile, BusinessTrustProfile, TopicProfile, PersonalizationProfile
├── Features: FeatureScore and nine named score models
├── Reasoning: DecisionInput, Decision, DecisionTrace
├── Validation: ValidationResult, ValidationError
└── Output: OutputRow, OutputFile
```

All models use `ConfigDict(frozen=True, extra="forbid")`. They serialize with
Pydantic's `model_dump`/`model_dump_json` and expose JSON Schema through
`model_json_schema()`.

## Dependency graph

```text
value_objects + enums
          ↓
       core models
          ↓
       context models
          ↓
retrieval / personalization / features
          ↓
      DecisionInput
          ↓
     Decision + Trace
          ↓
     OutputRow / OutputFile
```

The graph flows from scalar contracts to aggregates. Models import only lower
layers, which avoids circular dependencies and lets every module communicate
through stable typed values.

## Design decisions

- `StrEnum` provides closed vocabularies while keeping JSON values compatible
  with the external contract.
- `Annotated` value objects centralize identifier, score, count, and timezone-
  aware timestamp validation.
- Tuples represent immutable collections at module boundaries.
- `extra="forbid"` prevents silent schema drift.
- `DecisionInput` contains context, evidence, personalization, and features;
  it does not contain a model client or prompt.
- `DecisionTrace` is a data contract for auditability, not an explanation
  algorithm.
- Media context has optional extracted text and transcript fields, but Phase 1
  provides no producer for either field.

## Extension strategy

Later phases should add adapters and services that consume these models. They
must not add persistence, parsing, retrieval, feature calculations, or model
provider clients to the model package. New enum values require an explicit
contract review; new optional fields require a compatibility review; breaking
changes require a versioned migration.

## Example

```python
from datetime import UTC, datetime

from app.models import ConversationType, Message

message = Message(
    message_id="msg_123",
    user_id="user_42",
    conversation_id="conversation_7",
    conversation_type=ConversationType.PERSONAL,
    created_at=datetime.now(UTC),
)
```
