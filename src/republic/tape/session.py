"""Tape session helpers for Republic."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any, TYPE_CHECKING

from any_llm.types.completion import ChatCompletion, ChatCompletionChunk, ReasoningEffort

from republic.tape.context import TapeContext
from republic.tape.entries import TapeEntry
from republic.tape.query import TapeQuery
from republic.tools.schema import ToolInput

if TYPE_CHECKING:
    from republic.clients.chat import ChatClient


class Tape:
    """Stateful chat and tape access bound to a tape name."""

    def __init__(
        self,
        name: str,
        chat: ChatClient,
        *,
        context: TapeContext | None = None,
    ) -> None:
        self._name = name
        self._chat = chat
        self._context_override = context

    def __repr__(self) -> str:
        return f"<Tape name={self._name}>"

    def __call__(self, prompt: str | None = None, **kwargs: Any) -> str:
        return self.create(prompt, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def context(self) -> TapeContext:
        return self._context_override or self._chat._default_context

    @context.setter
    def context(self, value: TapeContext | None) -> None:
        self._context_override = value

    def entries(self) -> list[TapeEntry]:
        return self._chat._read_entries(self._name)

    def messages(self) -> list[dict[str, Any]]:
        return self._chat._read_messages(self._name, context=self._context_override)

    def append(self, entry: TapeEntry) -> None:
        self._chat._append_entry(self._name, entry)

    def query(self) -> TapeQuery:
        return self._chat._query_tape(self._name)

    def reset(self) -> None:
        self._chat._reset_tape(self._name)

    def handoff(self, name: str, *, state: dict[str, Any] | None = None, **meta: Any) -> list[TapeEntry]:
        return self._chat._handoff(self._name, name, state=state, **meta)

    def create(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        context = self._context_override
        return self._chat._create(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        context = self._context_override
        return self._chat._stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        context = self._context_override
        return self._chat._raw(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def stream_raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatCompletionChunk]:
        context = self._context_override
        return self._chat._stream_raw(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def tool_calls(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        context = self._context_override
        return self._chat._tool_calls(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def tools_auto(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        context = self._context_override
        return self._chat._tools_auto(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def tools_auto_stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        context = self._context_override
        return self._chat._tools_auto_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def acreate(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        context = self._context_override
        return await self._chat._acreate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def astream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        context = self._context_override
        return await self._chat._astream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def astream_raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        context = self._context_override
        return await self._chat._astream_raw(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def atools_auto(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        context = self._context_override
        return await self._chat._atools_auto(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def atools_auto_stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        context = self._context_override
        return await self._chat._atools_auto_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            images=images,
            tape=self._name,
            context=context,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )
