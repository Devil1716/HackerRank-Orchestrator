# Example Decision Trace

This is a real trace captured from the checked-in dataset for `msg_091`. The
message contains an account-verification request and a six-digit login code.
The full packet is intentionally not printed here because it includes the
complete historical context; this excerpt preserves the actual model shape and
representative measured metadata.

```json
{
  "message_id": "msg_091",
  "trace_id": "78ae5823-544e-44a8-a722-1226a9ad371c",
  "feature_count": 25,
  "signal_count": 10,
  "feature_algorithm": "phase6-v1",
  "signal_algorithm": "phase6.5-v1",
  "stages": [
    {"component": "context", "inputs": ["message"], "outputs": ["MessageContext"]},
    {"component": "personalization", "inputs": ["MessageContext"], "outputs": ["PersonalizationProfile"]},
    {"component": "retrieval", "inputs": ["MessageContext", "PersonalizationProfile"], "outputs": ["EvidenceBundle"]},
    {"component": "features", "inputs": ["MessageContext", "PersonalizationProfile", "EvidenceBundle"], "outputs": ["DecisionFeatures"]},
    {"component": "signals", "inputs": ["DecisionFeatures"], "outputs": ["DecisionSignals"]}
  ],
  "validation": {"status": "passed", "errors": [], "repairs": 0}
}
```

The UUID and durations are execution metadata and therefore vary by run; the
component order, input/output contracts, algorithm versions, and validation
rules are deterministic.

