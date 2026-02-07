# Tools

Tools are Python callables or Pydantic models that the model can invoke. Use a tool-capable model for best results.

Example prerequisite: set `LLM_API_KEY` in your environment.

```python
from __future__ import annotations

import os

from pydantic import BaseModel

from republic import LLM, schema_from_model, tool

api_key = os.getenv("LLM_API_KEY")
if not api_key:
    raise RuntimeError("Set LLM_API_KEY before running this example.")

tool_model = os.getenv("REPUBLIC_TOOL_MODEL", "openrouter:openai/gpt-4o-mini")
llm = LLM(model=tool_model, api_key=api_key)

tape = llm.tape("tools")

@tool
def get_weather(city: str) -> str:
    return f"weather({city})"

result = tape.tools_auto("Call get_weather for Paris.", tools=[get_weather], max_tokens=32)
print(result.kind)
print(result.tool_results)

class WeatherRequest(BaseModel):
    city: str

schema = schema_from_model(WeatherRequest)
print(schema["function"]["name"])
```

## Tool Context

If a tool needs extra metadata, declare `context=True` and accept a `ToolContext` argument. Republic will pass run metadata and a mutable state dictionary.
