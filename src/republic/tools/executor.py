"""Tool execution helpers for Republic."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from republic.core.errors import ErrorKind
from republic.core.results import ErrorPayload, ToolExecution
from republic.tools.context import ToolContext
from republic.tools.schema import Tool, ToolInput, normalize_tools


class ToolExecutor:
    """Execute tool calls with predictable validation and serialization."""

    def execute(
        self,
        response: list[dict[str, Any]] | dict[str, Any] | str,
        tools: ToolInput = None,
        *,
        context: ToolContext | None = None,
    ) -> ToolExecution:
        tool_calls = self._normalize_response(response)

        tool_map = self._build_tool_map(tools)
        if not tool_map:
            if tool_calls:
                raise ErrorPayload(ErrorKind.TOOL, "No runnable tools are available.")
            return ToolExecution(tool_calls=[], tool_results=[])

        results: list[Any] = []
        for tool_response in tool_calls:
            results.append(self._handle_tool_response(tool_response, tool_map, context))

        return ToolExecution(tool_calls=tool_calls, tool_results=results)

    def _handle_tool_response(
        self,
        tool_response: Any,
        tool_map: dict[str, Tool],
        context: ToolContext | None,
    ) -> Any:
        if not isinstance(tool_response, dict):
            raise ErrorPayload(ErrorKind.INVALID_INPUT, "Each tool call must be an object.")
        tool_name = tool_response.get("function", {}).get("name")
        if not tool_name:
            raise ErrorPayload(ErrorKind.INVALID_INPUT, "Tool call is missing name.")
        tool_obj = tool_map.get(tool_name)
        if tool_obj is None:
            raise ErrorPayload(ErrorKind.TOOL, f"Unknown tool name: {tool_name}.")
        tool_args = tool_response.get("function", {}).get("arguments", {})
        tool_args = self._normalize_tool_args(tool_name, tool_args)
        try:
            if tool_obj.context:
                if context is None:
                    raise ErrorPayload(  # noqa: TRY301
                        ErrorKind.INVALID_INPUT, f"Tool '{tool_name}' requires context but none was provided."
                    )
                return tool_obj.run(context=context, **tool_args)
            return tool_obj.run(**tool_args)
        except ErrorPayload:
            raise
        except ValidationError as exc:
            raise ErrorPayload(
                ErrorKind.INVALID_INPUT,
                f"Tool '{tool_name}' argument validation failed.",
                details={"errors": exc.errors()},
            ) from exc
        except Exception as exc:
            raise ErrorPayload(
                ErrorKind.TOOL,
                f"Tool '{tool_name}' execution failed.",
                details={"error": repr(exc)},
            ) from exc

    def _normalize_response(
        self,
        response: list[dict[str, Any]] | dict[str, Any] | str,
    ) -> list[dict[str, Any]]:
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as exc:
                raise ErrorPayload(
                    ErrorKind.INVALID_INPUT,
                    "Tool response is not a valid JSON string.",
                    details={"error": str(exc)},
                ) from exc
        if isinstance(response, dict):
            response = [response]
        if not isinstance(response, list):
            raise ErrorPayload(ErrorKind.INVALID_INPUT, "Tool response must be a list of objects.")
        return response

    def _build_tool_map(self, tools: ToolInput) -> dict[str, Tool]:
        if tools is None:
            raise ErrorPayload(ErrorKind.INVALID_INPUT, "No tools provided.")
        try:
            toolset = normalize_tools(tools)
        except (ValueError, TypeError) as exc:
            raise ErrorPayload(ErrorKind.INVALID_INPUT, str(exc)) from exc

        return {tool_obj.name: tool_obj for tool_obj in toolset.runnable if tool_obj.name}

    def _normalize_tool_args(self, tool_name: str, tool_args: Any) -> dict[str, Any]:
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError as exc:
                raise ErrorPayload(
                    ErrorKind.INVALID_INPUT,
                    f"Tool '{tool_name}' arguments are not valid JSON.",
                ) from exc
        if isinstance(tool_args, dict):
            return dict(tool_args)
        raise ErrorPayload(
            ErrorKind.INVALID_INPUT,
            f"Tool '{tool_name}' arguments must be an object.",
        )
