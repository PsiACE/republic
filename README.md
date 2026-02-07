# Republic

Republic is a minimal, tape-first LLM client built on any-llm. It makes every message, tool call, error, and run detail explicit, so you can audit and replay safely.

## Highlights

- Tape is the single source of truth for every run.
- Structured outputs by default with explicit error handling.
- Small API surface and predictable behavior.

## Quickstart (60 seconds)

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

llm = LLM(model="openrouter:openrouter/free", api_key=api_key)
result = llm.chat.create("Say hello in one short sentence.", max_tokens=32)
print(result.value)
print(result.error)
```

## Concepts

- Tape records prompts, messages, tool calls, tool results, errors, and run metadata.
- Context selects which tape entries become prompt messages.
- Tools expose Python callables or Pydantic models to the model.

## Development

```bash
make check
make test
```

## License

Apache-2.0
