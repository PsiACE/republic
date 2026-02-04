"""Chat helpers for Republic."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from any_llm.types.completion import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage, ReasoningEffort

from republic.core.errors import ErrorKind, RepublicError
from republic.core.execution import LLMCore
from republic.tape.context import TapeContext, build_messages
from republic.tape.entries import TapeEntry
from republic.tape.handoff import HandoffHandler, HandoffPolicy
from republic.tape.query import TapeQuery
from republic.tape.store import InMemoryTapeStore, TapeStore
from republic.tools.executor import ToolExecutor
from republic.tools.schema import ToolInput, ToolSet, normalize_tools

MessageInput = dict[str, Any] | ChatCompletionMessage


@dataclass(frozen=True)
class PreparedChat:
    payload: list[dict[str, Any]]
    new_messages: list[dict[str, Any]]
    toolset: ToolSet
    tape: str | None
    should_update: bool

    @property
    def tools_payload(self) -> list[dict[str, Any]] | None:
        return self.toolset.payload


@dataclass
class _StreamState:
    collected: list[str] = field(default_factory=list)
    tool_state: dict[int, dict[str, Any]] = field(default_factory=dict)

    def text(self) -> str:
        return "".join(self.collected)


class ChatClient:
    """Chat operations with predictable return types."""

    def __init__(
        self,
        core: LLMCore,
        tool_executor: ToolExecutor,
        store: TapeStore | None = None,
        context: TapeContext | None = None,
        handoff_handler: HandoffHandler | None = None,
        handoff_policy: HandoffPolicy | None = None,
    ) -> None:
        self._core = core
        self._tool_executor = tool_executor
        self._tape_store = store or InMemoryTapeStore()
        self._default_context = context or TapeContext()
        self._handoff_handler = handoff_handler
        self._handoff_policy = handoff_policy

    def _reject_reserved_kwargs(self, kwargs: dict[str, Any], *reserved: str) -> None:
        for key in reserved:
            if key in kwargs:
                raise RepublicError(ErrorKind.INVALID_INPUT, f"'{key}' is not supported in this method.")

    def _reject_tape_kwarg(self, kwargs: dict[str, Any]) -> None:
        if "tape" in kwargs:
            raise RepublicError(
                ErrorKind.INVALID_INPUT,
                "Use llm.tape(name) for stateful chat.",
            )

    def _validate_chat_input(
        self,
        *,
        prompt: str | None,
        messages: list[MessageInput] | None,
        system_prompt: str | None,
        images: Sequence[str] | str | None,
        tape: str | None,
    ) -> None:
        if prompt is not None and messages is not None:
            raise RepublicError(
                ErrorKind.INVALID_INPUT,
                "Provide either prompt or messages, not both.",
            )
        if prompt is None and messages is None:
            raise RepublicError(
                ErrorKind.INVALID_INPUT,
                "Either prompt or messages is required.",
            )
        if messages is not None:
            if system_prompt is not None:
                raise RepublicError(
                    ErrorKind.INVALID_INPUT,
                    "system_prompt is not supported with messages. Include it in messages instead.",
                )
            if images is not None:
                raise RepublicError(
                    ErrorKind.INVALID_INPUT,
                    "images are not supported with messages. Include image content in messages instead.",
                )
            if tape is not None:
                raise RepublicError(
                    ErrorKind.INVALID_INPUT,
                    "tape is not supported with messages.",
                )
        if images is not None and prompt is None:
            raise RepublicError(
                ErrorKind.INVALID_INPUT,
                "images require prompt to be set.",
            )

    def _prepare_messages(
        self,
        prompt: str | None,
        system_prompt: str | None,
        images: Sequence[str] | str | None,
        tape: str | None,
        messages: list[MessageInput] | None,
        context: TapeContext | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        self._validate_chat_input(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
        )
        if messages is not None:
            payload = [m.model_dump(exclude_none=True) if isinstance(m, ChatCompletionMessage) else m for m in messages]
            return payload, []

        if prompt is None:
            raise RepublicError(ErrorKind.INVALID_INPUT, "prompt is required when messages is not provided")

        user_content: Any = prompt
        if images:
            image_list = [images] if isinstance(images, str) else list(images)
            content = [{"type": "text", "text": prompt}]
            content.extend({"type": "image_url", "image_url": {"url": url}} for url in image_list)
            user_content = content

        user_message = {"role": "user", "content": user_content}

        if tape is None:
            if system_prompt:
                return [{"role": "system", "content": system_prompt}, user_message], []
            return [user_message], []

        history = self._read_messages(tape, context=context)
        new_messages: list[dict[str, Any]] = []
        if system_prompt and not any(msg.get("role") == "system" for msg in history):
            new_messages.append({"role": "system", "content": system_prompt})
        new_messages.append(user_message)
        return [*history, *new_messages], new_messages

    def _prepare_request(
        self,
        *,
        prompt: str | None,
        system_prompt: str | None,
        images: Sequence[str] | str | None,
        tape: str | None,
        messages: list[MessageInput] | None,
        context: TapeContext | None = None,
        tools: ToolInput,
        require_tools: bool = False,
        require_runnable: bool = False,
    ) -> PreparedChat:
        if require_tools and not tools:
            raise RepublicError(ErrorKind.INVALID_INPUT, "tools are required for this operation.")

        messages_payload, new_messages = self._prepare_messages(
            prompt,
            system_prompt,
            images,
            tape,
            messages,
            context=context,
        )
        toolset = self._normalize_tools(tools)

        if require_runnable:
            try:
                toolset.require_runnable()
            except ValueError as exc:
                raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)) from exc

        should_update = tape is not None and messages is None
        return PreparedChat(
            payload=messages_payload,
            new_messages=new_messages,
            toolset=toolset,
            tape=tape,
            should_update=should_update,
        )

    def _read_messages(
        self,
        tape: str,
        *,
        context: TapeContext | None = None,
    ) -> list[dict[str, Any]]:
        entries = self._context_entries(tape)
        active_context = context or self._default_context
        return build_messages(entries, active_context)

    def _context_entries(self, tape: str) -> list[TapeEntry]:
        return self._read_entries(tape)

    def _append_tape_messages(self, tape: str, messages: list[dict[str, Any]]) -> None:
        for message in messages:
            self._tape_store.append(tape, TapeEntry.message(message))

    def _append_tool_events(
        self,
        tape: str,
        tool_calls: list[dict[str, Any]] | None,
        tool_result: str | None,
    ) -> None:
        if tool_calls:
            self._tape_store.append(tape, TapeEntry(0, "tool_call", {"calls": tool_calls}))
        if tool_result is not None:
            self._tape_store.append(tape, TapeEntry(0, "tool_result", {"result": tool_result}))

    def _update_tape(
        self,
        prepared: PreparedChat,
        response_text: str,
        *,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_result: str | None = None,
    ) -> None:
        if prepared.tape is None:
            return
        self._append_tape_messages(prepared.tape, prepared.new_messages)
        self._append_tool_events(prepared.tape, tool_calls, tool_result)
        self._tape_store.append(
            prepared.tape,
            TapeEntry.message({"role": "assistant", "content": response_text}),
        )

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        if isinstance(response, ChatCompletion):
            if not response.choices:
                return ""
            message = response.choices[0].message
            return message.content or ""
        return ""

    def _extract_tool_calls(self, response: Any) -> list[dict[str, Any]]:
        if not isinstance(response, ChatCompletion):
            return []
        if not response.choices:
            return []
        tool_calls = response.choices[0].message.tool_calls or []
        calls = []
        for tool_call in tool_calls:
            calls.append({
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                }
            })
        return calls

    def _text_or_retry(
        self,
        response: Any,
        *,
        provider_name: str,
        model_id: str,
        attempt: int,
        prepared: PreparedChat,
    ) -> Any:
        text = self._extract_text(response)
        if text:
            if prepared.should_update:
                self._update_tape(prepared, text)
            return text
        empty_error = RepublicError(ErrorKind.TEMPORARY, f"{provider_name}:{model_id}: empty response")
        self._core.log_error(empty_error, provider_name, model_id, attempt)
        return self._core.RETRY

    @staticmethod
    def _accumulate_tool_calls(tool_state: dict[int, dict[str, Any]], tool_calls: Sequence[Any]) -> None:
        for tool_call in tool_calls:
            index = getattr(tool_call, "index", None)
            if index is None:
                index = len(tool_state)
            entry = tool_state.setdefault(index, {"function": {"name": "", "arguments": ""}})

            call_id = getattr(tool_call, "id", None)
            if call_id:
                entry["id"] = call_id
            call_type = getattr(tool_call, "type", None)
            if call_type:
                entry["type"] = call_type

            function = getattr(tool_call, "function", None)
            if function is None:
                continue
            name = getattr(function, "name", None)
            if name:
                entry["function"]["name"] = name
            arguments = getattr(function, "arguments", None)
            if arguments:
                entry["function"]["arguments"] += arguments

    @staticmethod
    def _finalize_tool_calls(tool_state: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
        return [tool_state[idx] for idx in sorted(tool_state)]

    def _handle_chunk(self, chunk: ChatCompletionChunk, state: _StreamState) -> str:
        if not chunk.choices:
            return ""
        delta = chunk.choices[0].delta
        content = delta.content or ""
        if content:
            state.collected.append(content)

        tool_calls = getattr(delta, "tool_calls", None)
        if tool_calls:
            self._accumulate_tool_calls(state.tool_state, tool_calls)
        return content

    def _normalize_tools(self, tools: ToolInput) -> ToolSet:
        try:
            return normalize_tools(tools)
        except ValueError as exc:
            raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)).with_cause(exc) from exc
        except TypeError as exc:
            raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)).with_cause(exc) from exc

    def __call__(self, prompt: str | None = None, **kwargs: Any) -> str:
        return self.create(prompt, **kwargs)

    def _run_sync(
        self,
        prepared: PreparedChat,
        *,
        model: str | None,
        provider: str | None,
        max_tokens: int | None,
        stream: bool,
        reasoning_effort: ReasoningEffort | None,
        kwargs: dict[str, Any],
        on_response: Any,
    ) -> Any:
        return self._core.run_chat_sync(
            messages_payload=prepared.payload,
            tools_payload=prepared.tools_payload,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=stream,
            reasoning_effort=reasoning_effort,
            tool_count=len(prepared.tools_payload or []),
            kwargs=kwargs,
            on_response=on_response,
        )

    async def _run_async(
        self,
        prepared: PreparedChat,
        *,
        model: str | None,
        provider: str | None,
        max_tokens: int | None,
        stream: bool,
        reasoning_effort: ReasoningEffort | None,
        kwargs: dict[str, Any],
        on_response: Any,
    ) -> Any:
        return await self._core.run_chat_async(
            messages_payload=prepared.payload,
            tools_payload=prepared.tools_payload,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=stream,
            reasoning_effort=reasoning_effort,
            tool_count=len(prepared.tools_payload or []),
            kwargs=kwargs,
            on_response=on_response,
        )

    def _stream_text(
        self,
        response: Iterator[ChatCompletionChunk],
        *,
        prepared: PreparedChat,
        provider: str,
        model: str,
    ) -> Iterator[str]:
        state = _StreamState()
        with self._core.span("republic.llm.stream", provider=provider, model=model):
            for chunk in response:
                content = self._handle_chunk(chunk, state)
                if content:
                    yield content

        if prepared.should_update and prepared.tape and state.collected:
            self._update_tape(prepared, state.text())

    async def _stream_text_async(
        self,
        response: AsyncIterator[ChatCompletionChunk],
        *,
        prepared: PreparedChat,
        provider: str,
        model: str,
    ) -> AsyncIterator[str]:
        state = _StreamState()
        with self._core.span("republic.llm.stream", provider=provider, model=model):
            async for chunk in response:
                content = self._handle_chunk(chunk, state)
                if content:
                    yield content

        if prepared.should_update and prepared.tape and state.collected:
            self._update_tape(prepared, state.text())

    def _stream_text_with_tools(
        self,
        response: Iterator[ChatCompletionChunk],
        *,
        prepared: PreparedChat,
        tools: Sequence[Any],
        provider: str,
        model: str,
    ) -> Iterator[str]:
        state = _StreamState()
        tool_result: str | None = None
        tool_calls: list[dict[str, Any]] | None = None

        with self._core.span("republic.llm.stream", provider=provider, model=model, tool_count=len(tools)):
            for chunk in response:
                content = self._handle_chunk(chunk, state)
                if content:
                    yield content

        if state.tool_state:
            tool_calls = self._finalize_tool_calls(state.tool_state)
            result = self._tool_executor.execute(tool_calls, tools=tools)
            if result is not None:
                tool_result = result
                yield result

        if prepared.should_update and prepared.tape:
            if state.collected:
                self._update_tape(
                    prepared,
                    state.text(),
                    tool_calls=tool_calls,
                    tool_result=tool_result,
                )
            elif tool_result is not None:
                self._update_tape(
                    prepared,
                    tool_result,
                    tool_calls=tool_calls,
                    tool_result=tool_result,
                )

    async def _stream_text_with_tools_async(
        self,
        response: AsyncIterator[ChatCompletionChunk],
        *,
        prepared: PreparedChat,
        tools: Sequence[Any],
        provider: str,
        model: str,
    ) -> AsyncIterator[str]:
        state = _StreamState()
        tool_result: str | None = None
        tool_calls: list[dict[str, Any]] | None = None

        with self._core.span("republic.llm.stream", provider=provider, model=model, tool_count=len(tools)):
            async for chunk in response:
                content = self._handle_chunk(chunk, state)
                if content:
                    yield content

        if state.tool_state:
            tool_calls = self._finalize_tool_calls(state.tool_state)
            result = self._tool_executor.execute(tool_calls, tools=tools)
            if result is not None:
                tool_result = result
                yield result

        if prepared.should_update and prepared.tape:
            if state.collected:
                self._update_tape(
                    prepared,
                    state.text(),
                    tool_calls=tool_calls,
                    tool_result=tool_result,
                )
            elif tool_result is not None:
                self._update_tape(
                    prepared,
                    tool_result,
                    tool_calls=tool_calls,
                    tool_result=tool_result,
                )

    def create(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_tape_kwarg(kwargs)
        return self._create(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _create(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=None,
        )

        def _handle(response: Any, provider_name: str, model_id: str, attempt: int) -> Any:
            return self._text_or_retry(
                response,
                provider_name=provider_name,
                model_id=model_id,
                attempt=attempt,
                prepared=prepared,
            )

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        self._reject_tape_kwarg(kwargs)
        return self._stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=None,
        )

        def _handle(response: Any, provider_name: str, model_id: str, _attempt: int) -> Any:
            return self._stream_text(
                response,
                prepared=prepared,
                provider=provider_name,
                model=model_id,
            )

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        self._reject_tape_kwarg(kwargs)
        return self._raw(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
        )

        def _handle(response: Any, _provider_name: str, _model_id: str, _attempt: int) -> Any:
            return response

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def stream_raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatCompletionChunk]:
        self._reject_tape_kwarg(kwargs)
        return self._stream_raw(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _stream_raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatCompletionChunk]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
        )

        def _handle(response: Any, _provider_name: str, _model_id: str, _attempt: int) -> Any:
            return response

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def tool_calls(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        self._reject_tape_kwarg(kwargs)
        return self._tool_calls(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _tool_calls(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
            require_tools=True,
        )

        def _handle(response: Any, _provider_name: str, _model_id: str, _attempt: int) -> Any:
            return self._extract_tool_calls(response)

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def tools_auto(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_tape_kwarg(kwargs)
        return self._tools_auto(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _tools_auto(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
            require_tools=True,
            require_runnable=True,
        )

        def _handle(response: Any, provider_name: str, model_id: str, attempt: int) -> Any:
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                result = self._tool_executor.execute(tool_calls, tools=prepared.toolset.runnable)
                if result is not None and prepared.should_update:
                    self._update_tape(
                        prepared,
                        result,
                        tool_calls=tool_calls,
                        tool_result=result,
                    )
                return result
            return self._text_or_retry(
                response,
                provider_name=provider_name,
                model_id=model_id,
                attempt=attempt,
                prepared=prepared,
            )

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def tools_auto_stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        self._reject_tape_kwarg(kwargs)
        return self._tools_auto_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    def _tools_auto_stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
            require_tools=True,
            require_runnable=True,
        )

        def _handle(response: Any, provider_name: str, model_id: str, _attempt: int) -> Any:
            return self._stream_text_with_tools(
                response,
                prepared=prepared,
                tools=prepared.toolset.runnable,
                provider=provider_name,
                model=model_id,
            )

        return self._run_sync(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def acreate(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_tape_kwarg(kwargs)
        return await self._acreate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def _acreate(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=None,
        )

        def _handle(response: Any, provider_name: str, model_id: str, attempt: int) -> Any:
            return self._text_or_retry(
                response,
                provider_name=provider_name,
                model_id=model_id,
                attempt=attempt,
                prepared=prepared,
            )

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def astream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._reject_tape_kwarg(kwargs)
        return await self._astream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def _astream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=None,
        )

        def _handle(response: Any, provider_name: str, model_id: str, _attempt: int) -> Any:
            return self._stream_text_async(
                response,
                prepared=prepared,
                provider=provider_name,
                model=model_id,
            )

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def araw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            tools=tools,
        )

        def _handle(response: Any, _provider_name: str, _model_id: str, _attempt: int) -> Any:
            return response

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def astream_raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        self._reject_tape_kwarg(kwargs)
        return await self._astream_raw(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def _astream_raw(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
        )

        def _handle(response: Any, _provider_name: str, _model_id: str, _attempt: int) -> Any:
            return response

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def atool_calls(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            tools=tools,
            require_tools=True,
        )

        def _handle(response: Any, _provider_name: str, _model_id: str, _attempt: int) -> Any:
            return self._extract_tool_calls(response)

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def atools_auto(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_tape_kwarg(kwargs)
        return await self._atools_auto(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def _atools_auto(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
            require_tools=True,
            require_runnable=True,
        )

        def _handle(response: Any, provider_name: str, model_id: str, attempt: int) -> Any:
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                result = self._tool_executor.execute(tool_calls, tools=prepared.toolset.runnable)
                if result is not None and prepared.should_update:
                    self._update_tape(
                        prepared,
                        result,
                        tool_calls=tool_calls,
                        tool_result=result,
                    )
                return result
            return self._text_or_retry(
                response,
                provider_name=provider_name,
                model_id=model_id,
                attempt=attempt,
                prepared=prepared,
            )

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=False,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def atools_auto_stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._reject_tape_kwarg(kwargs)
        return await self._atools_auto_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            messages=messages,
            max_tokens=max_tokens,
            images=images,
            tools=tools,
            reasoning_effort=reasoning_effort,
            **kwargs,
        )

    async def _atools_auto_stream(
        self,
        prompt: str | None = None,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        messages: list[MessageInput] | None = None,
        max_tokens: int | None = None,
        images: Sequence[str] | str | None = None,
        tape: str | None = None,
        context: TapeContext | None = None,
        tools: ToolInput = None,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            tape=tape,
            messages=messages,
            context=context,
            tools=tools,
            require_tools=True,
            require_runnable=True,
        )

        def _handle(response: Any, provider_name: str, model_id: str, _attempt: int) -> Any:
            return self._stream_text_with_tools_async(
                response,
                prepared=prepared,
                tools=prepared.toolset.runnable,
                provider=provider_name,
                model=model_id,
            )

        return await self._run_async(
            prepared,
            model=model,
            provider=provider,
            max_tokens=max_tokens,
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    def _reset_tape(self, name: str) -> None:
        self._tape_store.reset(name)

    def _list_tapes(self) -> list[str]:
        return self._tape_store.list_tapes()

    def _query_tape(self, name: str) -> TapeQuery:
        return TapeQuery(name, self._tape_store)

    def _read_entries(self, name: str) -> list[TapeEntry]:
        return self._tape_store.read(name) or []

    def _append_entry(self, name: str, entry: TapeEntry) -> None:
        self._tape_store.append(name, entry)

    def _set_default_context(self, context: TapeContext) -> None:
        self._default_context = context

    def _handoff(
        self,
        tape: str,
        name: str,
        *,
        state: dict[str, Any] | None = None,
        **meta: Any,
    ) -> list[TapeEntry]:
        if self._handoff_policy is not None:
            allowed = self._handoff_policy.allow(tape=tape, name=name, state=state, meta=meta)
            if not allowed:
                return []
        handler = self._handoff_handler
        if handler is None:
            entries = [TapeEntry.anchor(name, state=state, **meta)]
        else:
            entries = handler.build_entries(tape, name, state, meta)
        for entry in entries:
            self._tape_store.append(tape, entry)
        return entries
