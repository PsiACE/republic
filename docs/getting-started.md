# Getting Started

## Installation

```bash
pip install republic
```

## Quick Start

```python
from republic import LLM

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
print(llm.chat.create("Who are you?"))
print(llm.chat("Who are you?"))
```

## Provider and Model

Republic only accepts `provider:model`. The legacy `provider/model` format is not supported.

```python
from republic import LLM

llm = LLM(provider="openai", model="gpt-4o-mini", api_key="<OPENAI_API_KEY>")
print(llm.chat.create("Summarize this in one sentence."))
```
