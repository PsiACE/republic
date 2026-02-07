"""Tape session helpers for Republic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from republic.core.results import AsyncTextStream, StructuredOutput, TextStream, ToolAutoResult
from republic.tape.context import ContextSelection, TapeContext
from republic.tape.entries import TapeEntry
from republic.tape.query import QueryResult, TapeQuery

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

    def __call__(self, prompt: str | None = None, **kwargs: Any) -> StructuredOutput:
        return self.create(prompt, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def context(self) -> TapeContext:
        return self._context_override or self._chat.default_context

    @context.setter
    def context(self, value: TapeContext | None) -> None:
        self._context_override = value

    def entries(self) -> list[TapeEntry]:
        return self._chat.read_entries(self._name)

    def messages(self) -> ContextSelection:
        return self._chat.read_messages(self._name, context=self._context_override)

    def append(self, entry: TapeEntry) -> None:
        self._chat.append_entry(self._name, entry)

    def query(self) -> TapeQuery:
        return self._chat.query_tape(self._name)

    def reset(self) -> None:
        self._chat.reset_tape(self._name)

    def handoff(self, name: str, *, state: dict[str, Any] | None = None, **meta: Any) -> list[TapeEntry]:
        return self._chat.handoff(self._name, name, state=state, **meta)

    def create(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> StructuredOutput:
        context = self._context_override
        return self._chat.create(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            **kwargs,
        )

    async def create_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> StructuredOutput:
        context = self._context_override
        return await self._chat.create_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
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
        tools: Any = None,
        **kwargs: Any,
    ) -> ToolAutoResult:
        context = self._context_override
        return self._chat.tools_auto(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            tools=tools,
            **kwargs,
        )

    async def tools_auto_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        tools: Any = None,
        **kwargs: Any,
    ) -> ToolAutoResult:
        context = self._context_override
        return await self._chat.tools_auto_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            tools=tools,
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
        tools: Any = None,
        **kwargs: Any,
    ) -> StructuredOutput:
        context = self._context_override
        return self._chat.tool_calls(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            tools=tools,
            **kwargs,
        )

    async def tool_calls_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        tools: Any = None,
        **kwargs: Any,
    ) -> StructuredOutput:
        context = self._context_override
        return await self._chat.tool_calls_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            tools=tools,
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
        **kwargs: Any,
    ) -> TextStream:
        context = self._context_override
        return self._chat.stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            **kwargs,
        )

    async def stream_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncTextStream:
        context = self._context_override
        return await self._chat.stream_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            **kwargs,
        )

    def stream_events(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        max_tokens: int | None = None,
        tools: Any = None,
        **kwargs: Any,
    ):
        context = self._context_override
        return self._chat.stream_events(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
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
        max_tokens: int | None = None,
        tools: Any = None,
        **kwargs: Any,
    ):
        context = self._context_override
        return await self._chat.stream_events_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            tape=self._name,
            context=context,
            tools=tools,
            **kwargs,
        )

    def results(self) -> QueryResult:
        return self.query().all()
