# Design Principles and Tradeoffs

Republic is derived from litAI and keeps its minimal framework approach. It also borrows pydantic-ai's emphasis on explicit validation and structured results, while delegating provider abstraction to any-llm.

## Principles

- **Explicit over implicit**: every run is recorded in Tape, including errors and metadata.
- **Minimal surface area**: fewer entry points, clearer semantics, easier maintenance.
- **Structured by default**: outputs are wrapped in structured results with explicit error payloads.
- **Composable primitives**: build workflows on Tape, Tools, and Context instead of a monolithic framework.
- **Provider-agnostic core**: any-llm handles model and provider specifics.

## Tradeoffs

- Not a full agent framework: no built-in planning, orchestration, or multi-agent coordination.
- Less automation: more manual composition in exchange for predictability.
- Stronger boundaries: higher-level workflows live in application code, not the core client.

## Influence Summary

- litAI: minimal framework style and direct, readable abstractions.
- pydantic-ai: explicit validation boundaries and structured outputs.
- any-llm: unified provider/model interface and SDK isolation.
