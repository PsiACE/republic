# republic

[![Release](https://img.shields.io/github/v/release/psiace/republic)](https://img.shields.io/github/v/release/psiace/republic)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/republic/main.yml?branch=main)](https://github.com/psiace/republic/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/psiace/republic/branch/main/graph/badge.svg)](https://codecov.io/gh/psiace/republic)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/republic)](https://img.shields.io/github/commit-activity/m/psiace/republic)
[![License](https://img.shields.io/github/license/psiace/republic)](https://img.shields.io/github/license/psiace/republic)

An explicit LLM client and router with append-only history and controllable context.

Republic has one state primitive: a tape. A tape is an append-only log of messages and anchors.
You decide what goes into context, where a phase starts, and how handoff works. No hidden memory.

The idea is inspired by punch tape: a linear, immutable record you can slice into deterministic context windows.
It keeps the system simple, auditable, and easy to hand off between humans and agents.

Visit https://getrepublic.org for concepts, guides, and API reference.

- One entry point (`LLM`) with predictable behavior
- Tape-first state with explicit anchors and selection
- Provider-agnostic routing, retries, and fallbacks
- Typed tools with optional execution
- Streaming-first ergonomics
- Clear extension points for storage and observability

We like LitAI's pragmatic feel. Republic is derived from it, and we hope you like it too.

This project is derived from [lightning-ai/litai](https://github.com/lightning-ai/litai).

## Requirements

- Python 3.11+

## Installation

```bash
pip install republic
# Or, with uv
uv add republic
```

## Quick Start

```python
import os

from republic import LLM

llm = LLM(
    model="openrouter:openrouter/free",
    api_key=os.environ["LLM_API_KEY"],
    client_args={
        "default_headers": {
            "HTTP-Referer": "https://getrepublic.org",
            "X-Title": "republic docs",
        }
    },
)

print(llm.chat("Give me a one-sentence overview of Republic."))

notes = llm.tape("notes")
print(notes("Remember this for later."))
print(notes.messages())

for chunk in llm.chat.stream("Write a 5-word line about light."):
    print(chunk, end="")
```

Tool calling requires a tool-capable model. See the docs for tool examples and model guidance.

## Development

See `CONTRIBUTING.md` for local setup, testing, and release guidance.

## License

Apache 2.0
