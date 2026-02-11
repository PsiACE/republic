"""Tape session view helpers for Republic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from republic.core.results import (
    AsyncStreamEvents,
    AsyncTextStream,
    StreamEvents,
    TextStream,
    ToolAutoResult,
)
from republic.tape.context import TapeContext
from republic.tape.entries import TapeEntry
from republic.tape.query import TapeQuery
from republic.tools.schema import ToolInput

if TYPE_CHECKING:
    from republic.llm import LLM
    from republic.tape.manager import TapeManager


class Tape:
    """A scoped LLM session that interacts with a specific tape."""

    def __init__(
        self,
        name: str,
        manager: TapeManager,
        *,
        llm: LLM,
        context: TapeContext | None = None,
    ) -> None:
        self._name = name
        self._manager = manager
        self._llm = llm
        self._local_context = context

    def __repr__(self) -> str:
        return f"<Tape name={self._name}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def context(self) -> TapeContext:
        return self._local_context or self._manager.default_context

    @context.setter
    def context(self, value: TapeContext | None) -> None:
        self._local_context = value

    def read_entries(self) -> list[TapeEntry]:
        return self._manager.read_entries(self._name)

    def read_messages(self, *, context: TapeContext | None = None) -> list[dict[str, Any]]:
        active_context = context or self.context
        return self._manager.read_messages(self._name, context=active_context)

    def append(self, entry: TapeEntry) -> None:
        self._manager.append_entry(self._name, entry)

    def query(self) -> TapeQuery:
        return self._manager.query_tape(self._name)

    def reset(self) -> None:
        self._manager.reset_tape(self._name)

    def handoff(self, name: str, *, state: dict[str, Any] | None = None, **meta: Any) -> list[TapeEntry]:
        return self._manager.handoff(self._name, name, state=state, **meta)

    def chat(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        return self._llm.chat(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
            **kwargs,
        )

    async def chat_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        return await self._llm.chat_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
            **kwargs,
        )

    def tool_calls(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._llm.tool_calls(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
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
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return await self._llm.tool_calls_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
            tools=tools,
            **kwargs,
        )

    def run_tools(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> ToolAutoResult:
        return self._llm.run_tools(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
            tools=tools,
            **kwargs,
        )

    async def run_tools_async(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> ToolAutoResult:
        return await self._llm.run_tools_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
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
        messages: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> TextStream:
        return self._llm.stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
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
    ) -> AsyncTextStream:
        return await self._llm.stream_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
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
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> StreamEvents:
        return self._llm.stream_events(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
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
        tools: ToolInput = None,
        **kwargs: Any,
    ) -> AsyncStreamEvents:
        return await self._llm.stream_events_async(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            tape=self._name,
            context=self.context,
            tools=tools,
            **kwargs,
        )
