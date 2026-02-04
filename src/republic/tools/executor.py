"""Tool execution helpers for Republic."""

from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any, Callable, ContextManager, Dict, List, Optional, Sequence, Union

from republic.core.errors import ErrorKind, RepublicError
from republic.tools.schema import ToolInput, normalize_tools

SpanFactory = Callable[..., ContextManager[None]]


class ToolExecutor:
    """Execute tool calls with predictable validation and serialization."""

    def __init__(self, span: Optional[SpanFactory] = None) -> None:
        self._span = span or (lambda *args, **kwargs: nullcontext())

    def execute(self, response: Union[List[dict], dict, str], tools: ToolInput = None) -> Optional[str]:
        if tools is None:
            raise RepublicError(ErrorKind.INVALID_INPUT, "No tools provided.")

        tool_calls = self._normalize_response(response)
        tool_map = self._build_tool_map(tools)

        results: List[Any] = []
        for tool_response in tool_calls:
            if not isinstance(tool_response, dict):
                raise RepublicError(ErrorKind.INVALID_INPUT, "Tool response must be an object.")
            tool_name = tool_response.get("function", {}).get("name")
            if not tool_name:
                raise RepublicError(ErrorKind.INVALID_INPUT, "Tool response is missing a function name.")
            if tool_name not in tool_map:
                raise RepublicError(ErrorKind.INVALID_INPUT, f"Tool '{tool_name}' is not available.")
            tool_args = tool_response.get("function", {}).get("arguments", {})
            tool_args = self._normalize_tool_args(tool_name, tool_args)

            tool_callable = tool_map[tool_name]
            try:
                with self._span("republic.tool.call", tool=tool_name):
                    results.append(tool_callable(**tool_args))
            except Exception as exc:
                raise RepublicError(ErrorKind.TOOL, f"Tool '{tool_name}' execution failed.").with_cause(exc) from exc

        if not results:
            return None
        if len(results) > 1:
            return self._serialize_tool_result(results)
        return self._serialize_tool_result(results[0])

    def _normalize_response(self, response: Union[List[dict], dict, str]) -> List[dict]:
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

    def _build_tool_map(self, tools: ToolInput) -> Dict[str, Callable[..., Any]]:
        try:
            toolset = normalize_tools(tools)
        except (ValueError, TypeError) as exc:
            raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)).with_cause(exc) from exc

        tool_map = {tool_obj.name: tool_obj.run for tool_obj in toolset.runnable if tool_obj.name}
        if not tool_map:
            raise RepublicError(ErrorKind.INVALID_INPUT, "No callable tools available for execution.")
        return tool_map

    def _normalize_tool_args(self, tool_name: str, tool_args: Any) -> Dict[str, Any]:
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                raise RepublicError(
                    ErrorKind.INVALID_INPUT,
                    f"Tool arguments for '{tool_name}' are not valid JSON.",
                )
        if isinstance(tool_args, dict):
            return {k: v for k, v in tool_args.items() if v is not None}
        raise RepublicError(ErrorKind.INVALID_INPUT, f"Tool arguments for '{tool_name}' must be an object.")

    def _serialize_tool_result(self, result: Any) -> str:
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result)
        except TypeError as exc:
            raise RepublicError(ErrorKind.TOOL, "Tool result is not JSON serializable.").with_cause(exc) from exc
