"""Tool helpers for Republic."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union

from pydantic import BaseModel, TypeAdapter

ModelT = TypeVar("ModelT", bound=BaseModel)


def _to_snake_case(name: str) -> str:
    return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")


def _callable_name(func: Callable[..., Any]) -> str:
    name = getattr(func, "__name__", None)
    if isinstance(name, str) and name:
        return name
    return func.__class__.__name__


def _schema_from_annotation(annotation: Any) -> Dict[str, Any]:
    """Convert Python type annotations to JSON schema via Pydantic."""
    if annotation is inspect._empty:
        annotation = Any
    try:
        return TypeAdapter(annotation).json_schema()
    except Exception as exc:
        raise ValueError(f"Failed to build JSON schema for type: {annotation!r}") from exc


def _schema_from_signature(signature: inspect.Signature) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    required: List[str] = []
    for param in signature.parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        properties[param.name] = _schema_from_annotation(param.annotation)
        if param.default is param.empty:
            required.append(param.name)
    schema: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _validate_tool_schema(tool_schema: Dict[str, Any]) -> str:
    if tool_schema.get("type") != "function":
        raise ValueError("Tool schema must have type='function'.")
    function = tool_schema.get("function")
    if not isinstance(function, dict):
        raise ValueError("Tool schema must include a 'function' object.")
    name = function.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Tool schema must include a non-empty function name.")
    if "parameters" not in function:
        raise ValueError("Tool schema must include function parameters.")
    return name


@dataclass(frozen=True)
class Tool:
    """A Tool is a callable unit the model can invoke."""

    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable[..., Any]] = None

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def as_tool(self, json_mode: bool = False) -> Union[str, Dict[str, Any]]:
        schema = self.schema()
        if json_mode:
            return json.dumps(schema, indent=2)
        return schema

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self.handler is None:
            raise TypeError(f"Tool '{self.name}' is schema-only and cannot be executed.")
        return self.handler(*args, **kwargs)

    @classmethod
    def from_callable(
        cls,
        func: Callable[..., Any],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "Tool":
        tool_name = name or _to_snake_case(_callable_name(func))
        tool_description = description if description is not None else (inspect.getdoc(func) or "")
        parameters = _schema_from_signature(inspect.signature(func))
        return cls(name=tool_name, description=tool_description, parameters=parameters, handler=func)

    @classmethod
    def from_model(cls, model: type[ModelT], handler: Optional[Callable[[ModelT], Any]] = None) -> "Tool":
        if handler is None:
            raise TypeError("Tool.from_model requires a handler. Use schema_from_model for schema-only tools.")
        return tool_from_model(model, handler)

    @classmethod
    def convert_tools(cls, tools: ToolInput) -> List["Tool"]:
        if not tools:
            return []
        if isinstance(tools, ToolSet):
            return tools.runnable
        if any(isinstance(tool_item, dict) for tool_item in tools):
            raise TypeError("Schema-only tools are not supported in convert_tools.")
        toolset = normalize_tools(tools)
        return toolset.runnable


@dataclass(frozen=True)
class ToolSet:
    """Normalized tools with schema payload and runnable implementations."""

    schemas: List[Dict[str, Any]]
    runnable: List[Tool]

    @property
    def payload(self) -> Optional[List[Dict[str, Any]]]:
        return self.schemas or None

    def require_runnable(self) -> None:
        if self.schemas and not self.runnable:
            raise ValueError("Schema-only tools cannot be executed.")

    @classmethod
    def from_tools(cls, tools: ToolInput) -> "ToolSet":
        return normalize_tools(tools)


def schema_from_model(
    model: type[ModelT],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a tool schema from a Pydantic model without making it runnable."""
    model_name = name or _to_snake_case(model.__name__)
    model_description = description if description is not None else (model.__doc__ or "")
    return {
        "type": "function",
        "function": {
            "name": model_name,
            "description": model_description,
            "parameters": model.model_json_schema(),
        },
    }


def tool_from_model(
    model: type[ModelT],
    handler: Callable[[ModelT], Any],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Tool:
    """Create a runnable Tool that validates inputs via a Pydantic model."""
    tool_name = name or _to_snake_case(model.__name__)
    tool_description = description if description is not None else (model.__doc__ or "")

    def _handler(*args: Any, **kwargs: Any) -> Any:
        parsed = model(*args, **kwargs)
        return handler(parsed)

    return Tool(name=tool_name, description=tool_description, parameters=model.model_json_schema(), handler=_handler)


ToolInput = Optional[Union[ToolSet, Sequence[Any]]]


def normalize_tools(tools: ToolInput) -> ToolSet:
    """Normalize tool-like objects into a ToolSet."""
    if tools is None:
        return ToolSet([], [])
    if isinstance(tools, ToolSet):
        return tools
    if isinstance(tools, Sequence) and any(isinstance(tool_item, ToolSet) for tool_item in tools):
        raise TypeError("ToolSet cannot be mixed with other tool definitions.")
    if not tools:
        return ToolSet([], [])

    schemas: List[Dict[str, Any]] = []
    runnable_tools: List[Tool] = []
    seen_names: set[str] = set()

    for tool_item in tools:
        if isinstance(tool_item, dict):
            tool_name = _validate_tool_schema(tool_item)
            if tool_name in seen_names:
                raise ValueError(f"Duplicate tool name: {tool_name}")
            seen_names.add(tool_name)
            schemas.append(tool_item)
            continue

        if isinstance(tool_item, Tool):
            tool_obj = tool_item
        elif callable(tool_item):
            tool_obj = Tool.from_callable(tool_item)
        else:
            raise TypeError(f"Unsupported tool type: {type(tool_item)}")

        if not tool_obj.name:
            raise ValueError("Tool name cannot be empty.")
        if tool_obj.name in seen_names:
            raise ValueError(f"Duplicate tool name: {tool_obj.name}")
        seen_names.add(tool_obj.name)
        schemas.append(tool_obj.schema())
        if tool_obj.handler is not None:
            runnable_tools.append(tool_obj)

    return ToolSet(schemas, runnable_tools)


def tool(
    func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Union[Tool, Callable[..., Any]]:
    """Decorator to convert a function into a Tool instance."""

    def _create_tool(f: Callable[..., Any]) -> Tool:
        return Tool.from_callable(f, name=name, description=description)

    if func is None:
        return _create_tool
    return _create_tool(func)
