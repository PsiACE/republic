"""Chat helpers for Republic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Sequence

from any_llm.types.completion import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage, ReasoningEffort

from republic.core.conversations import ConversationStore, InMemoryConversationStore
from republic.core.errors import ErrorKind, RepublicError
from republic.core.execution import LLMCore
from republic.tools.executor import ToolExecutor
from republic.tools.schema import ToolInput, ToolSet, normalize_tools

MessageInput = Dict[str, Any] | ChatCompletionMessage


@dataclass(frozen=True)
class PreparedChat:
    payload: List[Dict[str, Any]]
    new_messages: List[Dict[str, Any]]
    toolset: ToolSet
    conversation: Optional[str]
    should_update: bool

    @property
    def tools_payload(self) -> Optional[List[Dict[str, Any]]]:
        return self.toolset.payload


@dataclass
class _StreamState:
    collected: List[str] = field(default_factory=list)
    tool_state: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    def text(self) -> str:
        return "".join(self.collected)


class ChatClient:
    """Chat operations with predictable return types."""

    def __init__(
        self,
        core: LLMCore,
        tool_executor: ToolExecutor,
        store: Optional[ConversationStore] = None,
    ) -> None:
        self._core = core
        self._tool_executor = tool_executor
        self._store = store or InMemoryConversationStore()

    def _reject_reserved_kwargs(self, kwargs: Dict[str, Any], *reserved: str) -> None:
        for key in reserved:
            if key in kwargs:
                raise RepublicError(ErrorKind.INVALID_INPUT, f"'{key}' is not supported in this method.")

    def _validate_chat_input(
        self,
        *,
        prompt: Optional[str],
        messages: Optional[List[MessageInput]],
        system_prompt: Optional[str],
        images: Optional[Sequence[str] | str],
        conversation: Optional[str],
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
            if conversation is not None:
                raise RepublicError(
                    ErrorKind.INVALID_INPUT,
                    "conversation is not supported with messages.",
                )
        if images is not None and prompt is None:
            raise RepublicError(
                ErrorKind.INVALID_INPUT,
                "images require prompt to be set.",
            )

    def _prepare_messages(
        self,
        prompt: Optional[str],
        system_prompt: Optional[str],
        images: Optional[Sequence[str] | str],
        conversation: Optional[str],
        messages: Optional[List[MessageInput]],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        self._validate_chat_input(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
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

        if conversation is None:
            if system_prompt:
                return [{"role": "system", "content": system_prompt}, user_message], []
            return [user_message], []

        history = self._store.get(conversation) or []
        new_messages: List[Dict[str, Any]] = []
        if system_prompt and not any(msg.get("role") == "system" for msg in history):
            new_messages.append({"role": "system", "content": system_prompt})
        new_messages.append(user_message)
        return [*history, *new_messages], new_messages

    def _prepare_request(
        self,
        *,
        prompt: Optional[str],
        system_prompt: Optional[str],
        images: Optional[Sequence[str] | str],
        conversation: Optional[str],
        messages: Optional[List[MessageInput]],
        tools: ToolInput,
        require_tools: bool = False,
        require_runnable: bool = False,
    ) -> PreparedChat:
        if require_tools and not tools:
            raise RepublicError(ErrorKind.INVALID_INPUT, "tools are required for this operation.")

        messages_payload, new_messages = self._prepare_messages(prompt, system_prompt, images, conversation, messages)
        toolset = self._normalize_tools(tools)

        if require_runnable:
            try:
                toolset.require_runnable()
            except ValueError as exc:
                raise RepublicError(ErrorKind.INVALID_INPUT, str(exc)) from exc

        should_update = conversation is not None and messages is None
        return PreparedChat(
            payload=messages_payload,
            new_messages=new_messages,
            toolset=toolset,
            conversation=conversation,
            should_update=should_update,
        )

    def _update_conversation(self, prepared: PreparedChat, response_text: str) -> None:
        if prepared.conversation is None:
            return
        for message in prepared.new_messages:
            self._store.append(prepared.conversation, message)
        self._store.append(prepared.conversation, {"role": "assistant", "content": response_text})

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        if isinstance(response, ChatCompletion):
            if not response.choices:
                return ""
            message = response.choices[0].message
            return message.content or ""
        return ""

    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
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
                self._update_conversation(prepared, text)
            return text
        empty_error = RepublicError(ErrorKind.TEMPORARY, f"{provider_name}:{model_id}: empty response")
        self._core.log_error(empty_error, provider_name, model_id, attempt)
        return self._core.RETRY

    @staticmethod
    def _accumulate_tool_calls(tool_state: Dict[int, Dict[str, Any]], tool_calls: Sequence[Any]) -> None:
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
    def _finalize_tool_calls(tool_state: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    def __call__(self, prompt: Optional[str] = None, **kwargs: Any) -> str:
        return self.create(prompt, **kwargs)

    def _run_sync(
        self,
        prepared: PreparedChat,
        *,
        model: Optional[str],
        provider: Optional[str],
        max_tokens: Optional[int],
        stream: bool,
        reasoning_effort: Optional[ReasoningEffort],
        kwargs: Dict[str, Any],
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
        model: Optional[str],
        provider: Optional[str],
        max_tokens: Optional[int],
        stream: bool,
        reasoning_effort: Optional[ReasoningEffort],
        kwargs: Dict[str, Any],
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

        if prepared.should_update and prepared.conversation and state.collected:
            self._update_conversation(prepared, state.text())

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

        if prepared.should_update and prepared.conversation and state.collected:
            self._update_conversation(prepared, state.text())

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
        tool_result: Optional[str] = None

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

        if prepared.should_update and prepared.conversation:
            if state.collected:
                self._update_conversation(prepared, state.text())
            elif tool_result is not None:
                self._update_conversation(prepared, tool_result)

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
        tool_result: Optional[str] = None

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

        if prepared.should_update and prepared.conversation:
            if state.collected:
                self._update_conversation(prepared, state.text())
            elif tool_result is not None:
                self._update_conversation(prepared, tool_result)

    def create(
        self,
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> Iterator[ChatCompletionChunk]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
            tools=tools,
            require_tools=True,
            require_runnable=True,
        )

        def _handle(response: Any, provider_name: str, model_id: str, attempt: int) -> Any:
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                result = self._tool_executor.execute(tool_calls, tools=prepared.toolset.runnable)
                if result is not None and prepared.should_update:
                    self._update_conversation(prepared, result)
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "tools", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatCompletionChunk]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
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
            stream=True,
            reasoning_effort=reasoning_effort,
            kwargs=kwargs,
            on_response=_handle,
        )

    async def atool_calls(
        self,
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> str:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
            tools=tools,
            require_tools=True,
            require_runnable=True,
        )

        def _handle(response: Any, provider_name: str, model_id: str, attempt: int) -> Any:
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                result = self._tool_executor.execute(tool_calls, tools=prepared.toolset.runnable)
                if result is not None and prepared.should_update:
                    self._update_conversation(prepared, result)
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
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        messages: Optional[List[MessageInput]] = None,
        max_tokens: Optional[int] = None,
        images: Optional[Sequence[str] | str] = None,
        conversation: Optional[str] = None,
        tools: ToolInput = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._reject_reserved_kwargs(kwargs, "stream", "auto_call_tools", "full_response")
        prepared = self._prepare_request(
            prompt=prompt,
            system_prompt=system_prompt,
            images=images,
            conversation=conversation,
            messages=messages,
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

    def reset_conversation(self, name: str) -> None:
        self._store.reset(name)

    def list_conversations(self) -> List[str]:
        return self._store.list()

    def get_history(self, name: str, raw: bool = False) -> Optional[List[Dict[str, Any]]]:
        history = self._store.get(name)
        if history is None:
            return None
        if raw:
            return history
        return [{"role": msg.get("role"), "content": msg.get("content")} for msg in history]
