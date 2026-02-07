# Republic

Republic is a minimal, tape-first LLM client built on any-llm. Tape captures every message, tool call, error, and run detail so you can audit, replay, and debug with confidence.

## What It Solves

- You want a single append-only record of model behavior.
- You prefer structured outputs and explicit error handling.
- You want a small, predictable API instead of a large framework.

## Quick Start

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

llm = LLM(model="openrouter:openrouter/free", api_key=api_key)
result = llm.chat.create("Give me one short sentence.", max_tokens=32)
print(result.value)
```

## Recommended Path

1. Start with Getting Started for the full walkthrough.
2. Read Tape and Context to understand how prompts are built.
3. Use Tools, Text, Streaming, and Embeddings guides as needed.
