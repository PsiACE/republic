import pytest
from pydantic import BaseModel

from republic import Tool, ToolSet, schema_from_model, tool, tool_from_model
from republic.core import ErrorKind, RepublicError
from republic.tools import ToolExecutor


class TestToolSchema:
    def test_tool_schema(self):
        def get_weather(location: str, units: str = "celsius") -> str:
            """Get weather for location."""
            return f"Weather in {location} ({units})"

        tool_instance = Tool.from_callable(get_weather)
        schema = tool_instance.schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "get_weather"
        assert schema["function"]["description"] == "Get weather for location."
        assert "location" in schema["function"]["parameters"]["properties"]
        assert "units" in schema["function"]["parameters"]["properties"]

    def test_tool_decorator(self):
        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        assert isinstance(add, Tool)
        assert add.name == "add"
        assert add.description == "Add two numbers."
        assert add.run(1, 2) == 3


class TestToolModels:
    def test_schema_from_model_builds_tool_schema(self):
        class Weather(BaseModel):
            """Weather request."""

            location: str

        schema = schema_from_model(Weather)
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "weather"
        assert schema["function"]["description"] == "Weather request."
        assert "location" in schema["function"]["parameters"]["properties"]

    def test_tool_from_model_executes_handler(self):
        class Weather(BaseModel):
            location: str

        def handler(payload: Weather) -> str:
            return f"Weather in {payload.location} is sunny"

        weather_tool = tool_from_model(Weather, handler)
        assert weather_tool.run(location="Tokyo") == "Weather in Tokyo is sunny"

    def test_tool_from_model_schema_matches_model(self):
        class Weather(BaseModel):
            """Weather request."""

            location: str

        def handler(payload: Weather) -> dict:
            return {"location": payload.location}

        weather_tool = tool_from_model(Weather, handler)
        schema = weather_tool.schema()
        assert schema["function"]["name"] == "weather"
        assert "location" in schema["function"]["parameters"]["properties"]

    def test_tool_from_model_defaults_to_model_dump(self):
        class Weather(BaseModel):
            location: str

        weather_tool = Tool.from_model(Weather)
        assert weather_tool.run(location="Tokyo") == {"location": "Tokyo"}


class TestToolSets:
    def test_toolset_from_tools(self):
        @tool
        def add(a: int, b: int) -> int:
            return a + b

        toolset = ToolSet.from_tools([add])
        assert toolset.payload is not None
        assert toolset.runnable[0].name == "add"

    def test_toolset_rejects_mixing_with_list(self):
        @tool
        def add(a: int, b: int) -> int:
            return a + b

        toolset = ToolSet.from_tools([add])
        with pytest.raises(TypeError):
            ToolSet.from_tools([toolset, add])


class TestToolExecution:
    def test_tool_executor_rejects_duplicate_names(self):
        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        tool_schema = {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                    "required": ["a", "b"],
                },
            },
        }

        executor = ToolExecutor()
        response = {"function": {"name": "add", "arguments": "{}"}}
        with pytest.raises(RepublicError) as exc_info:
            executor.execute(response, tools=[tool_schema, add])
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_convert_tools_rejects_schema_only(self):
        tool_schema = {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                    "required": ["a", "b"],
                },
            },
        }

        with pytest.raises(TypeError):
            Tool.convert_tools([tool_schema])

    def test_tool_executor_accepts_toolset(self):
        @tool
        def add(a: int, b: int) -> int:
            return a + b

        toolset = ToolSet.from_tools([add])
        executor = ToolExecutor()
        response = {"function": {"name": "add", "arguments": '{"a": 1, "b": 2}'}}
        assert executor.execute(response, tools=toolset) == 3

    def test_tool_executor_drops_none(self):
        @tool
        def set_owner(owner_id: str | None = "missing") -> str:
            return owner_id or "missing"

        executor = ToolExecutor()
        response = {"function": {"name": "set_owner", "arguments": {"owner_id": None}}}
        assert executor.execute(response, tools=[set_owner]) == "missing"
