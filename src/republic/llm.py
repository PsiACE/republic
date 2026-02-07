"""Republic LLM facade."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any

from republic.__about__ import DEFAULT_MODEL
from republic.clients._internal import InternalOps
from republic.clients.chat import ChatClient
from republic.clients.embedding import EmbeddingClient
from republic.clients.text import TextClient
from republic.core.errors import ErrorKind, RepublicError
from republic.core.execution import LLMCore
from republic.tape import Tape, TapeContext, TapeStore
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
            error_classifier=error_classifier,
        )
        tool_executor = ToolExecutor()
        self.chat = ChatClient(
            self._core,
            tool_executor,
            store=tape_store,
            context=context,
        )
        self.tools = tool_executor
        self.text = TextClient(self.chat)
        self.embeddings = EmbeddingClient(self._core)
        self._internal = InternalOps(self._core)

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
        return self.chat.default_context

    @context.setter
    def context(self, value: TapeContext) -> None:
        self.chat._default_context = value

    def tape(self, name: str, *, context: TapeContext | None = None) -> Tape:
        return Tape(name, self.chat, context=context)

    def tapes(self) -> list[str]:
        return self.chat._tape_store.list_tapes()

    def if_(self, input_text: str, question: str):
        return self.text.if_(input_text, question)

    def classify(self, input_text: str, choices: list[str]):
        return self.text.classify(input_text, choices)

    async def if_async(self, input_text: str, question: str):
        return await self.text.if_async(input_text, question)

    async def classify_async(self, input_text: str, choices: list[str]):
        return await self.text.classify_async(input_text, choices)

    def embed(
        self,
        inputs: str | list[str],
        *,
        model: str | None = None,
        provider: str | None = None,
        **kwargs: Any,
    ):
        return self.embeddings.embed(inputs, model=model, provider=provider, **kwargs)

    async def embed_async(
        self,
        inputs: str | list[str],
        *,
        model: str | None = None,
        provider: str | None = None,
        **kwargs: Any,
    ):
        return await self.embeddings.embed_async(inputs, model=model, provider=provider, **kwargs)

    def stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        return self.chat.stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def stream_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ):
        return await self.chat.stream_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )

    def stream_events(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        tools: Any = None,
        **kwargs: Any,
    ):
        return self.chat.stream_events(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )

    async def stream_events_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        tools: Any = None,
        **kwargs: Any,
    ):
        return await self.chat.stream_events_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        )

    def __repr__(self) -> str:
        return (
            f"<LLM provider={self._core.provider} model={self._core.model} "
            f"fallback_models={self._core.fallback_models} max_retries={self._core.max_retries}>"
        )
