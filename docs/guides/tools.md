# Tools

Tools let you describe functions and optionally run them.

Tool calling requires a tool-capable model. The `openrouter/free` router may return models that do not support
tool calling, so use a fixed model for the examples below.

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

Single tool results return the raw value; multiple results return a JSON string list.

## Automatic Tool Execution

Automatic tool execution requires a tool-capable model. The `openrouter/free` router may return models that do not
support tool calling, so prefer a fixed model for production tools.

```python
result = llm.chat.tools_auto("What's the weather in Tokyo?", tools=[get_weather])
print(result)
```

## Tools with Tape

```python
tape = llm.tape("notes")
result = tape.tools_auto("What's the weather in Tokyo?", tools=[get_weather])
print(result)
```

## Typed Tools and Schemas

Note: Schema-only and runnable tools must use distinct `name` values to avoid conflicts.

```python
from pydantic import BaseModel
from republic import ToolSet, schema_from_model, tool_from_model

class WeatherSchema(BaseModel):
    """Weather request."""

    location: str

tool_schema = schema_from_model(WeatherSchema, name="weather_schema")

def handle_weather(payload: WeatherSchema) -> str:
    return f"Weather in {payload.location} is sunny"

typed_tool = tool_from_model(WeatherSchema, handle_weather, name="weather_tool")

toolset = ToolSet.from_tools([tool_schema, typed_tool])
print(toolset.payload)
```

`Tool.from_model` provides a default runnable tool that validates and returns `model_dump()`.

```python
from republic import Tool

tool = Tool.from_model(WeatherSchema)
print(tool.run(location="Tokyo"))
```
