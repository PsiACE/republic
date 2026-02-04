from __future__ import annotations

from typing import Any

import pytest
from any_llm.types.completion import ChatCompletion, ChatCompletionChunk

from republic import LLM, tool


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
                            "function": {"name": "get_weather", "arguments": '{"location": "Tokyo"}'},
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
        payloads.append({
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
        })
    return [ChatCompletionChunk.model_validate(payload) for payload in payloads]


def _make_mixed_tool_text_stream() -> list[ChatCompletionChunk]:
    text_chunks = _make_text_stream(["Hel", "lo"])
    tool_chunks = _make_tool_call_stream()
    return [text_chunks[0], tool_chunks[0], text_chunks[1]]


async def _async_iter(items: list[Any]):
    for item in items:
        yield item


class TestTapeChatUpdates:
    def test_tape_updates_with_text(self, stub_client):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini")
        tape = llm.tape("conv")

        assert tape.create("Hi") == "Hello"
        history = tape.messages()
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Hello"

    def test_tape_updates_with_tool_result(self, stub_client):
        stub_client.completion.return_value = _make_tool_call_response()

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        tape = llm.tape("conv")

        assert tape.tools_auto("Weather?", tools=[get_weather]) == "Weather in Tokyo is sunny"
        history = tape.messages()
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Weather in Tokyo is sunny"

    def test_tape_updates_with_tool_result_stream(self, stub_client):
        stub_client.completion.return_value = iter(_make_tool_call_stream())

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        tape = llm.tape("conv")

        result = list(tape.tools_auto_stream("Weather?", tools=[get_weather]))
        assert result == ["Weather in Tokyo is sunny"]
        history = tape.messages()
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Weather in Tokyo is sunny"

    def test_tools_auto_stream_prefers_text_for_tape(self, stub_client):
        stub_client.completion.return_value = iter(_make_mixed_tool_text_stream())

        @tool
        def get_weather(location: str) -> str:
            """Get the weather for a location."""
            return f"Weather in {location} is sunny"

        llm = LLM(model="openai:gpt-4o-mini")
        tape = llm.tape("conv")

        chunks = list(tape.tools_auto_stream("Weather?", tools=[get_weather]))

        assert chunks == ["Hel", "lo", "Weather in Tokyo is sunny"]
        history = tape.messages()
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_async_tape_stream_updates(self, stub_client):
        stub_client.acompletion.return_value = _async_iter(_make_text_stream(["Hel", "lo"]))

        llm = LLM(model="openai:gpt-4o-mini")
        tape = llm.tape("conv")

        stream = await tape.astream("Hi")
        assert [chunk async for chunk in stream] == ["Hel", "lo"]
        history = tape.messages()
        assert history[-1]["role"] == "assistant"
        assert history[-1]["content"] == "Hello"
