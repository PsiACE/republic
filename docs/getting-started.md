# Getting Started

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
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
tape = llm.tape("notes")

print(llm.chat.create("Who are you?"))
print(tape("Remember this for later."))
print(tape.messages())
```

`llm.chat` is stateless. `llm.tape(name)` gives you stateful chat with explicit history.

## Provider and Model

Republic only accepts `provider:model`. The legacy `provider/model` format is not supported.

```python
from republic import LLM

llm = LLM(provider="openai", model="gpt-4o-mini", api_key="<OPENAI_API_KEY>")
print(llm.chat.create("Summarize this in one sentence."))
```

## Next

- Learn the mental model in [Tape](concepts/tape.md) and [Context](concepts/context.md).
- Follow the practical recipes in [Chat](guides/chat.md) and [Tools](guides/tools.md).
