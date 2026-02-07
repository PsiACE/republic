# Text Helpers

Text helpers wrap tool calls to provide structured boolean and classification outputs. Use a tool-capable model for reliable behavior.

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

tool_model = os.getenv("REPUBLIC_TOOL_MODEL", "openrouter:openai/gpt-4o-mini")
llm = LLM(model=tool_model, api_key=api_key)

decision = llm.if_("ship it", "Is this positive?")
print(decision.value)
print(decision.error)

label = llm.classify("urgent outage", ["bug", "feature", "support"])
print(label.value)
print(label.error)
```

## Error Handling

Every helper returns a `StructuredOutput` with `value` and `error`. Check `error` when you need explicit control over failure modes.
