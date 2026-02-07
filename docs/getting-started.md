# Getting Started

## Install

```bash
pip install republic
```

## Choose a Model

Republic expects the `provider:model` format. For OpenRouter, the provider is `openrouter` and the model can be `openrouter/free` or any OpenRouter-supported model.

## Your First Call

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

llm = LLM(model="openrouter:openrouter/free", api_key=api_key)
result = llm.chat.create("Summarize this in one sentence.", max_tokens=32)
print(result.value)
```

## Tape in Two Steps

1. Bind a tape name.
2. Call `tape.create(...)` and inspect `tape.entries()`.

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

llm = LLM(model="openrouter:openrouter/free", api_key=api_key)

tape = llm.tape("notes")
result = tape.create("Write a short note.", max_tokens=32)
print(result.value)
print(tape.entries())
```

## Tools and Structured Output

Use a tool-capable model when you need tool calls or structured text helpers.

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM, tool

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

tool_model = os.getenv("REPUBLIC_TOOL_MODEL", "openrouter:openai/gpt-4o-mini")
llm = LLM(model=tool_model, api_key=api_key)

tape = llm.tape("tools")

@tool
def echo(text: str) -> str:
    return text

result = tape.tools_auto("Call echo with 'hi'.", tools=[echo], max_tokens=32)
print(result.kind)
print(result.tool_results)
```
