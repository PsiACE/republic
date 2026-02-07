"""Tool execution helpers for Republic."""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from typing import Any

from republic.core.errors import ErrorKind, RepublicError
from republic.tools.schema import ToolInput, normalize_tools

SpanFactory = Callable[..., AbstractContextManager[None]]


class ToolExecutor:
    """Execute tool calls with predictable validation and serialization."""

    def __init__(self, span: SpanFactory | None = None) -> None:
        self._span = span or (lambda *args, **kwargs: nullcontext())
        self._skip = object()
        self._abort = object()

    def execute(self, response: list[dict] | dict | str, tools: ToolInput = None) -> Any | None:
        if tools is None:
            raise RepublicError(ErrorKind.INVALID_INPUT, "No tools provided.")

        tool_calls = self._normalize_response(response)
        tool_map = self._build_tool_map(tools)
        if not tool_map:
            return None

        results: list[Any] = []
        for tool_response in tool_calls:
            outcome = self._handle_tool_response(tool_response, tool_map)
            if outcome is self._abort:
                return None
            if outcome is self._skip:
                continue
            results.append(outcome)

        if not results:
            return None
        if len(results) > 1:
            return self._serialize_tool_result(results)
        return results[0]

    def _handle_tool_response(self, tool_response: Any, tool_map: dict[str, Callable[..., Any]]) -> Any:
        if not isinstance(tool_response, dict):
            return self._skip
        tool_name = tool_response.get("function", {}).get("name")
        if not tool_name:
            return self._skip
        tool_callable = tool_map.get(tool_name)
        if tool_callable is None:
            return self._skip
        tool_args = tool_response.get("function", {}).get("arguments", {})
        tool_args = self._normalize_tool_args(tool_name, tool_args)
        if tool_args is None:
            return self._abort
        try:
            with self._span("republic.tool.call", tool=tool_name):
                return tool_callable(**tool_args)
        except Exception as exc:
            raise RepublicError(ErrorKind.TOOL, f"Tool '{tool_name}' execution failed.").with_cause(exc) from exc

    def _normalize_response(self, response: list[dict] | dict | str) -> list[dict]:
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as exc:
                raise RepublicError(ErrorKind.INVALID_INPUT, "Tool response is not a valid JSON string.").with_cause(
                    exc
                ) from exc
        if isinstance(response, dict):
            response = [response]
        if not isinstance(response, list):
            raise RepublicError(ErrorKind.INVALID_INPUT, "Tool response must be a list of objects.")
        return response

    def _build_tool_map(self, tools: ToolInput) -> dict[str, Callable[..., Any]]:
        try:
            toolset = normalize_tools(tools)
        except (ValueError, TypeError) as exc:
            raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)).with_cause(exc) from exc

        tool_map = {tool_obj.name: tool_obj.run for tool_obj in toolset.runnable if tool_obj.name}
        return tool_map

    def _normalize_tool_args(self, tool_name: str, tool_args: Any) -> dict[str, Any] | None:
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                return None
        if isinstance(tool_args, dict):
            return {key: value for key, value in tool_args.items() if value is not None}
        return None

    def _serialize_tool_result(self, result: Any) -> str:
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result)
        except TypeError as exc:
            raise RepublicError(ErrorKind.TOOL, "Tool result is not JSON serializable.").with_cause(exc) from exc
