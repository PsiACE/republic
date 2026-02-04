# Tools

## Define a Tool

```python
from republic import LLM, tool

@tool
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"Weather in {location} is sunny"

llm = LLM(model="openai:gpt-4o-mini", api_key="<OPENAI_API_KEY>")
```

## Manual Tool Execution

```python
tool_calls = llm.chat.tool_calls("What's the weather in Tokyo?", tools=[get_weather])
result = llm.tools.execute(tool_calls, tools=[get_weather])
print(result)
```

## Automatic Tool Execution

```python
result = llm.chat.tools_auto("What's the weather in Tokyo?", tools=[get_weather])
print(result)
```

## Typed Tools and Schemas

```python
from pydantic import BaseModel
from republic import ToolSet, schema_from_model, tool_from_model

class WeatherSchema(BaseModel):
    """Weather request."""

    location: str

tool_schema = schema_from_model(WeatherSchema)

def handle_weather(payload: WeatherSchema) -> str:
    return f"Weather in {payload.location} is sunny"

typed_tool = tool_from_model(WeatherSchema, handle_weather)

toolset = ToolSet.from_tools([tool_schema, typed_tool])
print(toolset.payload)
```
