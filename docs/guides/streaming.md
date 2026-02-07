# Streaming

Use `stream` for text-only streaming. Use `stream_events` to receive text deltas, tool calls, tool results, usage, and a final summary event.

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from republic import LLM

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

stream_model = os.getenv("REPUBLIC_STREAM_MODEL", "openrouter:openai/gpt-4o-mini")
llm = LLM(model=stream_model, api_key=api_key)

stream = llm.stream("Reply with two short words.", max_tokens=16)
text = "".join(chunk for chunk in stream)
print(text)
print(stream.error)

for event in llm.stream_events("Say hi.", max_tokens=16):
    if event.kind == "text":
        print(event.data["delta"], end="")
```

## Error Handling

Streaming helpers attach errors to the stream object and include error events in the event stream. Always check `error` after iteration.
