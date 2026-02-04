# republic

[![Release](https://img.shields.io/github/v/release/psiace/republic)](https://img.shields.io/github/v/release/psiace/republic)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/republic/main.yml?branch=main)](https://github.com/psiace/republic/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/psiace/republic/branch/main/graph/badge.svg)](https://codecov.io/gh/psiace/republic)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/republic)](https://img.shields.io/github/commit-activity/m/psiace/republic)
[![License](https://img.shields.io/github/license/psiace/republic)](https://img.shields.io/github/license/psiace/republic)

A minimal, explicit LLM router and agent toolkit built on top of Mozilla's any-llm.

Visit https://getrepublic.org for concepts, guides, and API reference.

- Small surface area with predictable behavior
- Provider-agnostic routing and fallbacks
- Tape-first state with explicit handoff and context control
- Typed tools with optional auto-execution
- Streaming-first ergonomics
- Clear extension points for storage and observability

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

from republic import LLM, tool

@tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"Weather in {location} is sunny"

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

print(notes.tools_auto("What's the weather in Tokyo?", tools=[get_weather]))
for chunk in llm.chat.stream("Write a 5-word line about light."):
    print(chunk, end="")
```

Tool calling requires a tool-capable model. See the docs for tool examples and model guidance.

## Development

See `CONTRIBUTING.md` for local setup, testing, and release guidance.

## License

Apache 2.0

---

> This project is derived from [lightning-ai/litai](https://github.com/lightning-ai/litai); we hope you like it too.
