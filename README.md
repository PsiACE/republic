# republic

[![Release](https://img.shields.io/github/v/release/psiace/republic)](https://img.shields.io/github/v/release/psiace/republic)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/republic/main.yml?branch=main)](https://github.com/psiace/republic/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/psiace/republic/branch/main/graph/badge.svg)](https://codecov.io/gh/psiace/republic)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/republic)](https://img.shields.io/github/commit-activity/m/psiace/republic)
[![License](https://img.shields.io/github/license/psiace/republic)](https://img.shields.io/github/license/psiace/republic)

A minimal, explicit LLM router and agent toolkit built on top of Mozilla's any-llm.

- Small surface area with predictable behavior
- Provider-agnostic routing and fallbacks
- Typed tools with optional auto-execution
- Streaming-first ergonomics
- Clear extension points for storage and observability

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

Use `provider:model` when overriding:

```python
from republic import LLM

llm = LLM(provider="openai", model="gpt-4o-mini", api_key="<OPENAI_API_KEY>")
print(llm.chat.create("Summarize this in one sentence."))
```

Note: Republic only accepts `provider:model`.

## Development

See `CONTRIBUTING.md` for local setup, testing, and release guidance.

## License

Apache 2.0
