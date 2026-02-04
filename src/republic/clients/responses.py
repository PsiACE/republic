"""Responses API helpers for Republic."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any, Literal, overload

from any_llm.types.responses import Response, ResponseInputParam, ResponseStreamEvent
from openresponses_types import ResponseResource

from republic.core.errors import ErrorKind, RepublicError
from republic.core.execution import LLMCore
from republic.tools.schema import ToolInput, normalize_tools


class ResponsesClient:
    """OpenAI-style Responses API facade."""

    def __init__(self, core: LLMCore) -> None:
        self._core = core

    @staticmethod
    def _reject_stream(kwargs: dict[str, Any]) -> None:
        if "stream" in kwargs:
            raise RepublicError(ErrorKind.INVALID_INPUT, "'stream' is not supported in this method.")

    def _resolve_provider_model(self, model: str | None, provider: str | None) -> tuple[str, str]:
        if model is None and provider is None:
            return self._core.provider, self._core.model
        return self._core.resolve_model_provider(model or self._core.model, provider)

    def _prepare_tools(self, tools: ToolInput) -> list[dict[str, Any]] | None:
        try:
            toolset = normalize_tools(tools)
        except (ValueError, TypeError) as exc:
            raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)).with_cause(exc) from exc
        return toolset.payload

    @overload
    def _call(
        self,
        *,
        input_data: str | ResponseInputParam,
        model: str | None,
        provider: str | None,
        tools: ToolInput,
        stream: Literal[False],
        kwargs: dict[str, Any],
    ) -> ResponseResource | Response: ...

    @overload
    def _call(
        self,
        *,
        input_data: str | ResponseInputParam,
        model: str | None,
        provider: str | None,
        tools: ToolInput,
        stream: Literal[True],
        kwargs: dict[str, Any],
    ) -> Iterator[ResponseStreamEvent]: ...

    def _call(
        self,
        *,
        input_data: str | ResponseInputParam,
        model: str | None,
        provider: str | None,
        tools: ToolInput,
        stream: bool,
        kwargs: dict[str, Any],
    ) -> ResponseResource | Response | Iterator[ResponseStreamEvent]:
        provider_name, model_id = self._resolve_provider_model(model, provider)
        client = self._core.get_client(provider_name)
        tools_payload = self._prepare_tools(tools)
        try:
            with self._core.span("republic.llm.responses", provider=provider_name, model=model_id, stream=stream):
                return client.responses(
                    model=model_id,
                    input_data=input_data,
                    tools=tools_payload,
                    stream=stream,
                    **kwargs,
                )
        except Exception as exc:
            self._core.raise_wrapped(exc, provider_name, model_id)
            raise AssertionError("unreachable") from exc

    @overload
    async def _acall(
        self,
        *,
        input_data: str | ResponseInputParam,
        model: str | None,
        provider: str | None,
        tools: ToolInput,
        stream: Literal[False],
        kwargs: dict[str, Any],
    ) -> ResponseResource | Response: ...

    @overload
    async def _acall(
        self,
        *,
        input_data: str | ResponseInputParam,
        model: str | None,
        provider: str | None,
        tools: ToolInput,
        stream: Literal[True],
        kwargs: dict[str, Any],
    ) -> AsyncIterator[ResponseStreamEvent]: ...

    async def _acall(
        self,
        *,
        input_data: str | ResponseInputParam,
        model: str | None,
        provider: str | None,
        tools: ToolInput,
        stream: bool,
        kwargs: dict[str, Any],
    ) -> ResponseResource | Response | AsyncIterator[ResponseStreamEvent]:
        provider_name, model_id = self._resolve_provider_model(model, provider)
        client = self._core.get_client(provider_name)
        tools_payload = self._prepare_tools(tools)
        try:
            with self._core.span("republic.llm.responses", provider=provider_name, model=model_id, stream=stream):
                return await client.aresponses(
                    model=model_id,
                    input_data=input_data,
                    tools=tools_payload,
                    stream=stream,
                    **kwargs,
                )
        except Exception as exc:
            self._core.raise_wrapped(exc, provider_name, model_id)
            raise AssertionError("unreachable") from exc

    def create(
        self,
        input_data: str | ResponseInputParam,
        *,
        model: str | None = None,
        provider: str | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> ResponseResource | Response:
        self._reject_stream(kwargs)
        return self._call(
            input_data=input_data,
            model=model,
            provider=provider,
            tools=tools,
            stream=False,
            kwargs=kwargs,
        )

    def stream(
        self,
        input_data: str | ResponseInputParam,
        *,
        model: str | None = None,
        provider: str | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> Iterator[ResponseStreamEvent]:
        self._reject_stream(kwargs)
        return self._call(
            input_data=input_data,
            model=model,
            provider=provider,
            tools=tools,
            stream=True,
            kwargs=kwargs,
        )

    async def acreate(
        self,
        input_data: str | ResponseInputParam,
        *,
        model: str | None = None,
        provider: str | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> ResponseResource | Response:
        self._reject_stream(kwargs)
        return await self._acall(
            input_data=input_data,
            model=model,
            provider=provider,
            tools=tools,
            stream=False,
            kwargs=kwargs,
        )

    async def astream(
        self,
        input_data: str | ResponseInputParam,
        *,
        model: str | None = None,
        provider: str | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> AsyncIterator[ResponseStreamEvent]:
        self._reject_stream(kwargs)
        return await self._acall(
            input_data=input_data,
            model=model,
            provider=provider,
            tools=tools,
            stream=True,
            kwargs=kwargs,
        )
