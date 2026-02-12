from __future__ import annotations

import pytest
from pydantic import BaseModel

from republic import Tool, ToolContext, tool, tool_from_model
from republic.core.errors import ErrorKind
from republic.core.results import ErrorPayload
from republic.tools import ToolExecutor, normalize_tools


class Reminder(BaseModel):
    title: str


def test_tool_from_model_validates_payload() -> None:
    reminder_tool = tool_from_model(Reminder, lambda payload: payload.model_dump())
    executor = ToolExecutor()

    ok = executor.execute(
        [{"function": {"name": "reminder", "arguments": {"title": "buy milk"}}}],
        tools=[reminder_tool],
    )
    assert ok.error is None
    assert ok.tool_results == [{"title": "buy milk"}]

    with pytest.raises(ErrorPayload) as exc_info:
        executor.execute(
            [{"function": {"name": "reminder", "arguments": {"missing": "value"}}}],
            tools=[reminder_tool],
        )
    assert exc_info.value.kind == ErrorKind.INVALID_INPUT


def test_context_tool_requires_context() -> None:
    @tool(context=True)
    def write_note(title: str, context: ToolContext) -> str:
        context.state["title"] = title
        return title

    executor = ToolExecutor()
    calls = [{"function": {"name": "write_note", "arguments": {"title": "hello"}}}]

    with pytest.raises(ErrorPayload) as exc_info:
        executor.execute(calls, tools=[write_note])
    assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    ctx = ToolContext(tape="ops", run_id="run-1")
    ok = executor.execute(calls, tools=[write_note], context=ctx)
    assert ok.error is None
    assert ok.tool_results == ["hello"]
    assert ctx.state["title"] == "hello"


def test_normalize_tools_rejects_duplicate_names() -> None:
    @tool(name="echo")
    def echo_one(text: str) -> str:
        return text

    @tool(name="echo")
    def echo_two(text: str) -> str:
        return text

    with pytest.raises(ValueError):
        normalize_tools([echo_one, echo_two])


def test_convert_tools_rejects_schema_only_tools() -> None:
    schema_only = {
        "type": "function",
        "function": {
            "name": "schema_only",
            "description": "schema",
            "parameters": {"type": "object", "properties": {}},
        },
    }

    with pytest.raises(TypeError):
        Tool.convert_tools([schema_only])


def test_sync_execute_rejects_async_handler() -> None:
    @tool
    async def async_echo(text: str) -> str:
        return text

    executor = ToolExecutor()
    with pytest.raises(ErrorPayload) as exc_info:
        executor.execute(
            [{"function": {"name": "async_echo", "arguments": {"text": "hello"}}}],
            tools=[async_echo],
        )
    assert exc_info.value.kind == ErrorKind.INVALID_INPUT
    assert "execute_async" in exc_info.value.message


@pytest.mark.asyncio
async def test_execute_async_supports_async_handler() -> None:
    @tool
    async def async_echo(text: str) -> str:
        return f"async:{text}"

    @tool
    def sync_echo(text: str) -> str:
        return f"sync:{text}"

    executor = ToolExecutor()
    execution = await executor.execute_async(
        [
            {"function": {"name": "async_echo", "arguments": {"text": "hello"}}},
            {"function": {"name": "sync_echo", "arguments": {"text": "world"}}},
        ],
        tools=[async_echo, sync_echo],
    )
    assert execution.error is None
    assert execution.tool_results == ["async:hello", "sync:world"]
