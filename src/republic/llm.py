"""Republic LLM facade."""

from __future__ import annotations

import warnings
from collections.abc import Callable, Sequence
from typing import Any

from any_llm.types.completion import CreateEmbeddingResponse
from any_llm.types.model import Model

from republic.__about__ import DEFAULT_MODEL
from republic.clients.batch import BatchClient
from republic.clients.chat import ChatClient
from republic.clients.responses import ResponsesClient
from republic.clients.text import TextClient
from republic.core.errors import ErrorKind, RepublicError
from republic.core.execution import LLMCore
from republic.core.telemetry import span as logfire_span
from republic.tape import HandoffHandler, HandoffPolicy, Tape, TapeContext, TapeStore
from republic.tools.executor import ToolExecutor


class LLM:
    """Developer-first LLM client powered by any-llm."""

    def __init__(
        self,
        model: str | None = None,
        *,
        provider: str | None = None,
        fallback_models: list[str] | None = None,
        max_retries: int = 3,
        api_key: str | dict[str, str] | None = None,
        api_base: str | dict[str, str] | None = None,
        client_args: dict[str, Any] | None = None,
        verbose: int = 0,
        tape_store: TapeStore | None = None,
        context: TapeContext | None = None,
        handoff_handler: HandoffHandler | None = None,
        handoff_policy: HandoffPolicy | None = None,
        error_classifier: Callable[[Exception], ErrorKind | None] | None = None,
    ) -> None:
        if verbose not in (0, 1, 2):
            raise RepublicError(ErrorKind.INVALID_INPUT, "verbose must be 0, 1, or 2")
        if max_retries < 0:
            raise RepublicError(ErrorKind.INVALID_INPUT, "max_retries must be >= 0")

        if not model:
            model = DEFAULT_MODEL
            warnings.warn(f"No model was provided, defaulting to {model}", UserWarning, stacklevel=2)

        resolved_provider, resolved_model = LLMCore.resolve_model_provider(model, provider)

        self._core = LLMCore(
            provider=resolved_provider,
            model=resolved_model,
            fallback_models=fallback_models or [],
            max_retries=max_retries,
            api_key=api_key,
            api_base=api_base,
            client_args=client_args or {},
            verbose=verbose,
            span=self._span,
            error_classifier=error_classifier,
        )
        tool_executor = ToolExecutor(span=self._span)
        self.chat: ChatClient = ChatClient(
            self._core,
            tool_executor,
            store=tape_store,
            context=context,
            handoff_handler=handoff_handler,
            handoff_policy=handoff_policy,
        )
        self.responses: ResponsesClient = ResponsesClient(self._core)
        self.batch: BatchClient = BatchClient(self._core)
        self.tools: ToolExecutor = tool_executor
        self.text: TextClient = TextClient(self.chat)

    def _span(self, name: str, **attributes: Any):
        return logfire_span(name, **attributes)

    def _call_provider(self, provider_name: str, model_id: str, span_name: str, fn):
        client = self._core.get_client(provider_name)
        try:
            with self._core.span(span_name, provider=provider_name, model=model_id):
                return fn(client)
        except Exception as exc:
            self._core.raise_wrapped(exc, provider_name, model_id)

    async def _acall_provider(self, provider_name: str, model_id: str, span_name: str, fn):
        client = self._core.get_client(provider_name)
        try:
            with self._core.span(span_name, provider=provider_name, model=model_id):
                return await fn(client)
        except Exception as exc:
            self._core.raise_wrapped(exc, provider_name, model_id)

    @property
    def model(self) -> str:
        return self._core.model

    @property
    def provider(self) -> str:
        return self._core.provider

    @property
    def fallback_models(self) -> list[str]:
        return self._core.fallback_models

    @property
    def context(self) -> TapeContext:
        return self.chat._default_context

    @context.setter
    def context(self, value: TapeContext) -> None:
        self.chat._set_default_context(value)

    def tape(
        self,
        name: str,
        *,
        context: TapeContext | None = None,
    ) -> Tape:
        return Tape(name, self.chat, context=context)

    def tapes(self) -> list[str]:
        return self.chat._list_tapes()

    def embedding(
        self,
        inputs: str | list[str],
        *,
        model: str | None = None,
        provider: str | None = None,
        **kwargs: Any,
    ) -> CreateEmbeddingResponse:
        if model is None and provider is None:
            provider_name, model_id = self._core.provider, self._core.model
        else:
            provider_name, model_id = self._core.resolve_model_provider(model or self._core.model, provider)
        return self._call_provider(
            provider_name,
            model_id,
            "republic.llm.embedding",
            lambda client: client._embedding(model=model_id, inputs=inputs, **kwargs),
        )

    async def aembedding(
        self,
        inputs: str | list[str],
        *,
        model: str | None = None,
        provider: str | None = None,
        **kwargs: Any,
    ) -> CreateEmbeddingResponse:
        if model is None and provider is None:
            provider_name, model_id = self._core.provider, self._core.model
        else:
            provider_name, model_id = self._core.resolve_model_provider(model or self._core.model, provider)
        return await self._acall_provider(
            provider_name,
            model_id,
            "republic.llm.embedding",
            lambda client: client.aembedding(model=model_id, inputs=inputs, **kwargs),
        )

    def list_models(self, *, provider: str | None = None, **kwargs: Any) -> Sequence[Model]:
        provider_name = provider or self._core.provider
        return self._call_provider(
            provider_name,
            "-",
            "republic.llm.list_models",
            lambda client: client.list_models(**kwargs),
        )

    async def alist_models(self, *, provider: str | None = None, **kwargs: Any) -> Sequence[Model]:
        provider_name = provider or self._core.provider
        return await self._acall_provider(
            provider_name,
            "-",
            "republic.llm.list_models",
            lambda client: client.alist_models(**kwargs),
        )

    def __repr__(self) -> str:
        return (
            f"<LLM provider={self._core.provider} model={self._core.model} "
            f"fallback_models={self._core.fallback_models} max_retries={self._core.max_retries}>"
        )
