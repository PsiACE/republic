from __future__ import annotations

from republic.core.errors import ErrorKind
from republic.tools import Tool, ToolContext, ToolExecutor, tool


def test_tool_executor_runs_tool() -> None:
    @tool
    def greet(name: str) -> str:
        return f"hi {name}"

    executor = ToolExecutor()
    calls = [{"function": {"name": "greet", "arguments": {"name": "Ada"}}}]
    result = executor.execute(calls, tools=[greet])
    assert result.error is None
    assert result.tool_results == ["hi Ada"]


def test_tool_executor_missing_name() -> None:
    @tool
    def greet(name: str) -> str:
        return f"hi {name}"

    executor = ToolExecutor()
    calls = [{"function": {"arguments": {"name": "Ada"}}}]
    result = executor.execute(calls, tools=[greet])
    assert result.error is not None
    assert result.error.kind == ErrorKind.INVALID_INPUT


def test_tool_executor_context_required() -> None:
    def record(value: int, context: ToolContext) -> int:
        context.state["value"] = value
        return value

    record_tool = Tool.from_callable(record, context=True)

    executor = ToolExecutor()
    calls = [{"function": {"name": "record", "arguments": {"value": 3}}}]
    result = executor.execute(calls, tools=[record_tool])
    assert result.error is not None
    assert result.error.kind == ErrorKind.INVALID_INPUT

    result = executor.execute(calls, tools=[record_tool], context=ToolContext(tape=None, run_id="run"))
    assert result.error is None
    assert result.tool_results == [3]
