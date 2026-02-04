# republic

Republic is an explicit LLM client and router with append-only history and controllable context.

It gives you one state primitive: a tape. A tape is an append-only log of messages and anchors.
You decide what goes into context and where a phase starts. No hidden memory.

The mental model comes from punch tape: a linear record that you can slice into deterministic context windows.
That makes handoff and audit simple while keeping the API small.

We like LitAI's pragmatic feel. Republic is derived from it, and we hope you like it too.

## Getting Started

Start here: [Getting Started](getting-started.md)

## Core Idea

Tape makes state explicit. You choose the slice, not the framework.

## Concepts

- [Tape](concepts/tape.md)
- [Context](concepts/context.md)

## Guides

- [Chat](guides/chat.md)
- [Tools](guides/tools.md)
- [Responses](guides/responses.md)
- [Batch](guides/batch.md)

## Operations

- [Error Handling](operations/errors.md)
- [Observability](operations/observability.md)

## Reference

- [API Reference](reference/api.md)

---

> This project is derived from [lightning-ai/litai](https://github.com/lightning-ai/litai); we hope you like it too.
