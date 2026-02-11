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
