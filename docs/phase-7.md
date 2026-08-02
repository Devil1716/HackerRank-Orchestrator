# Phase 7 — Notification Router Agent

Phase 7 is the only AI boundary. `RouterAgent.decide` accepts one immutable
`DecisionPacket` and returns one immutable `Decision`. It has no repository,
retrieval, feature-engineering, OCR, speech, embedding, or statistics access.

Prompt construction is componentized into system, context, evidence, signal, and
instruction builders. `PromptAssembler` estimates tokens, truncates bounded
sections, and uses the versioned `router-prompt-v1` registry. Providers are
isolated behind one interface; OpenAI, Gemini, Ollama, vLLM, and Mock adapters are
available as seams, with transport injected rather than embedded in the agent.

Output parsing is strict Pydantic JSON validation. Invalid output receives one
structured repair attempt through the same provider, then fails explicitly.
Decision metadata records provider, latency, token usage, repair count, prompt and
decision versions. The Router Agent does not calculate confidence or alter the
deterministic signals; it only reasons over the packet.
