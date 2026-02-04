from __future__ import annotations

from typing import Any

import pytest
from any_llm.types.completion import ChatCompletion, ChatCompletionChunk

from republic import ErrorKind, LLM, RepublicError, ToolSet, tool


def _make_tool_call_response() -> ChatCompletion:
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"location": "Tokyo"}'},
    }
    payload = {
        "id": "chatcmpl_1",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": "tool_calls",
                "message": {"role": "assistant", "content": None, "tool_calls": [tool_call]},
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    return ChatCompletion.model_validate(payload)


def _make_tool_call_stream() -> list[ChatCompletionChunk]:
    payload = {
        "id": "chatcmpl_stream_1",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "delta": {
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": "{\"location\": \"Tokyo\"}"},
                        }
                    ]
                },
                "finish_reason": "tool_calls",
            }
        ],
    }
    return [ChatCompletionChunk.model_validate(payload)]


def _make_text_stream(chunks: list[str]) -> list[ChatCompletionChunk]:
    payloads = []
    for idx, content in enumerate(chunks):
        payloads.append(
            {
                "id": f"chatcmpl_stream_{idx}",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": "gpt-4o-mini",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": content},
                        "finish_reason": None,
                    }
                ],
            }
        )
    return [ChatCompletionChunk.model_validate(payload) for payload in payloads]


def _make_mixed_tool_text_stream() -> list[ChatCompletionChunk]:
    text_chunks = _make_text_stream(["Hel", "lo"])
    tool_chunks = _make_tool_call_stream()
    return [text_chunks[0], tool_chunks[0], text_chunks[1]]


async def _async_iter(items: list[Any]):
    for item in items:
        yield item


class TestChatBasics:
    def test_returns_text(self, stub_client):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.chat.create("Hi") == "Hello"

    def test_callable(self, stub_client):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.chat("Hi") == "Hello"

    def test_streams_text(self, stub_client):
        stub_client.completion.return_value = iter(_make_text_stream(["Hel", "lo"]))
        llm = LLM(model="openai:gpt-4o-mini")

        assert list(llm.chat.stream("Hi")) == ["Hel", "lo"]


class TestChatTools:
    def test_tool_calls_manual(self, stub_client):
        stub_client.completion.return_value = _make_tool_call_response()

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        tool_calls = llm.chat.tool_calls("Weather?", tools=[get_weather])

        assert tool_calls[0]["function"]["name"] == "get_weather"
        assert llm.tools.execute(tool_calls, tools=[get_weather]) == "Weather in Tokyo is sunny"

    def test_tools_auto(self, stub_client):
        stub_client.completion.return_value = _make_tool_call_response()

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        assert llm.chat.tools_auto("Weather?", tools=[get_weather]) == "Weather in Tokyo is sunny"

    def test_tools_auto_accepts_toolset(self, stub_client):
        stub_client.completion.return_value = _make_tool_call_response()

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        toolset = ToolSet.from_tools([get_weather])
        llm = LLM(model="openai:gpt-4o-mini")
        assert llm.chat.tools_auto("Weather?", tools=toolset) == "Weather in Tokyo is sunny"

    def test_tools_auto_stream(self, stub_client):
        stub_client.completion.return_value = iter(_make_tool_call_stream())

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        assert list(llm.chat.tools_auto_stream("Weather?", tools=[get_weather])) == ["Weather in Tokyo is sunny"]


class TestChatConversationUpdates:
    def test_conversation_updates_with_text(self, stub_client):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.chat.create("Hi", conversation="conv") == "Hello"
        history = llm.chat.get_history("conv")
        assert history is not None
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Hello"

    def test_conversation_updates_with_tool_result(self, stub_client):
        stub_client.completion.return_value = _make_tool_call_response()

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        assert llm.chat.tools_auto("Weather?", tools=[get_weather], conversation="conv") == "Weather in Tokyo is sunny"
        history = llm.chat.get_history("conv")
        assert history is not None
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Weather in Tokyo is sunny"

    def test_conversation_updates_with_tool_result_stream(self, stub_client):
        stub_client.completion.return_value = iter(_make_tool_call_stream())

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        result = list(llm.chat.tools_auto_stream("Weather?", tools=[get_weather], conversation="conv"))
        assert result == ["Weather in Tokyo is sunny"]
        history = llm.chat.get_history("conv")
        assert history is not None
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Weather in Tokyo is sunny"

    def test_tools_auto_stream_prefers_text_for_conversation(self, stub_client):
        stub_client.completion.return_value = iter(_make_mixed_tool_text_stream())

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        chunks = list(llm.chat.tools_auto_stream("Weather?", tools=[get_weather], conversation="conv"))

        assert chunks == ["Hel", "lo", "Weather in Tokyo is sunny"]
        history = llm.chat.get_history("conv")
        assert history is not None
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Hello"


class TestChatValidation:
    def test_chat_rejects_tools_kwarg(self, stub_client):
        stub_client.completion.return_value = "Hello"

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create("Weather?", tools=[get_weather])
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_auto_call_requires_callable_tools(self, stub_client):
        stub_client.completion.return_value = _make_tool_call_response()
        tool_schema = {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather.",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            },
        }

        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.tools_auto("Weather?", tools=[tool_schema])
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_prompt_and_messages_are_mutually_exclusive(self):
        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create(prompt="hi", messages=[{"role": "user", "content": "hi"}])
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_messages_disallow_system_prompt(self):
        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create(messages=[{"role": "user", "content": "hi"}], system_prompt="sys")
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_messages_disallow_images(self):
        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create(messages=[{"role": "user", "content": "hi"}], images="http://example.com/image.png")
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_messages_disallow_conversation(self):
        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create(messages=[{"role": "user", "content": "hi"}], conversation="conv")
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    def test_auto_call_tools_requires_tools(self):
        llm = LLM(model="openai:gpt-4o-mini")
        with pytest.raises(RepublicError) as exc_info:
            llm.chat.tools_auto(prompt="hi")
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT


class TestChatAsync:
    @pytest.mark.asyncio
    async def test_async_tools_auto_stream_updates_conversation(self, stub_client):
        stub_client.acompletion.return_value = _async_iter(_make_tool_call_stream())

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")

        stream = await llm.chat.atools_auto_stream("Weather?", tools=[get_weather], conversation="conv")
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        assert chunks == ["Weather in Tokyo is sunny"]
        history = llm.chat.get_history("conv")
        assert history is not None
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Weather in Tokyo is sunny"
