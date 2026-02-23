from __future__ import annotations

from types import SimpleNamespace

import pytest

from republic import LLM, tool
from republic.core.errors import ErrorKind
from republic.core.results import ErrorPayload

from .fakes import (
    make_chunk,
    make_response,
    make_responses_completed,
    make_responses_function_delta,
    make_responses_function_done,
    make_responses_response,
    make_responses_text_delta,
    make_responses_tool_call,
    make_tool_call,
)


def test_chat_retries_and_returns_text(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(RuntimeError("temporary failure"), make_response(text="ready"))

    llm = LLM(
        model="openai:gpt-4o-mini",
        api_key="dummy",
        max_retries=2,
        error_classifier=lambda _: ErrorKind.TEMPORARY,
    )

    out = llm.chat("Reply with ready", max_tokens=8)
    assert out == "ready"
    assert len(client.calls) == 2


def test_chat_uses_fallback_model(fake_anyllm) -> None:
    primary = fake_anyllm.ensure("openai")
    fallback = fake_anyllm.ensure("anthropic")

    primary.queue_completion(RuntimeError("primary down"))
    fallback.queue_completion(make_response(text="fallback ok"))

    llm = LLM(
        model="openai:gpt-4o-mini",
        fallback_models=["anthropic:claude-3-5-sonnet-latest"],
        max_retries=1,
        api_key={"openai": "x", "anthropic": "y"},
        error_classifier=lambda _: ErrorKind.TEMPORARY,
    )

    out = llm.chat("Ping")
    assert out == "fallback ok"
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


def test_chat_fallbacks_on_auth_error(fake_anyllm) -> None:
    class FakeAuthError(Exception):
        def __init__(self, message: str) -> None:
            super().__init__(message)
            self.status_code = 401

    primary = fake_anyllm.ensure("openai")
    fallback = fake_anyllm.ensure("openrouter")

    primary.queue_completion(FakeAuthError("invalid api key"))
    fallback.queue_completion(make_response(text="fallback ok"))

    llm = LLM(
        model="openai:gpt-4o-mini",
        fallback_models=["openrouter:openrouter/free"],
        max_retries=2,
        api_key={"openai": "bad", "openrouter": "ok"},
    )

    out = llm.chat("Ping")
    assert out == "fallback ok"
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


def test_chat_fallbacks_on_rate_limit_like_error(fake_anyllm) -> None:
    class FakeRateLimitError(Exception):
        def __init__(self, message: str) -> None:
            super().__init__(message)
            self.status_code = 429

    primary = fake_anyllm.ensure("openai")
    fallback = fake_anyllm.ensure("openrouter")

    primary.queue_completion(FakeRateLimitError("too many requests"))
    fallback.queue_completion(make_response(text="fallback ok"))

    llm = LLM(
        model="openai:gpt-4o-mini",
        fallback_models=["openrouter:openrouter/free"],
        max_retries=1,
        api_key={"openai": "x", "openrouter": "y"},
    )

    out = llm.chat("Ping")
    assert out == "fallback ok"
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


def test_tape_requires_anchor_then_records_full_run(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(make_response(text="step one"), make_response(text="step two"))

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")
    tape = llm.tape("ops")

    with pytest.raises(ErrorPayload) as exc_info:
        llm.chat("Investigate DB timeout", tape="ops")
    assert exc_info.value.kind == ErrorKind.NOT_FOUND
    assert len(client.calls) == 0

    tape.handoff("incident_42", state={"owner": "tier1"})
    first = llm.chat("Investigate DB timeout", tape="ops")
    second = llm.chat("Include rollback criteria", tape="ops")
    assert first == "step one"
    assert second == "step two"

    second_messages = client.calls[-1]["messages"]
    assert [message["role"] for message in second_messages] == ["user", "assistant", "user"]

    entries = tape.read_entries()
    kinds = [entry.kind for entry in entries]
    assert kinds[0] == "error"
    assert entries[0].payload["kind"] == ErrorKind.NOT_FOUND.value
    assert "anchor" in kinds
    assert kinds[-1] == "event"

    run_event = entries[-1]
    assert run_event.payload["name"] == "run"
    assert run_event.payload["data"]["status"] == "ok"


def test_tape_chat_shortcuts_bind_current_tape(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(make_response(text="step one"), make_response(text="step two"))

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")
    tape = llm.tape("ops")
    tape.handoff("incident_42")

    first = tape.chat("Investigate DB timeout")
    second = tape.chat("Include rollback criteria")
    assert first == "step one"
    assert second == "step two"

    second_messages = client.calls[-1]["messages"]
    assert [message["role"] for message in second_messages] == ["user", "assistant", "user"]


@tool
def echo(text: str) -> str:
    return text.upper()


@tool
async def async_echo(text: str) -> str:
    return text.upper()


def test_stream_events_carries_text_tools_usage_and_final(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(
        iter([
            make_chunk(text="Checking "),
            make_chunk(tool_calls=[make_tool_call("echo", '{"text":"to', call_id="call_1")]),
            make_chunk(
                tool_calls=[make_tool_call("echo", 'kyo"}', call_id="call_1")],
                usage={"total_tokens": 12},
            ),
        ])
    )

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")
    stream = llm.stream_events("Call echo for tokyo", tools=[echo])
    events = list(stream)

    kinds = [event.kind for event in events]
    assert "text" in kinds
    assert "tool_call" in kinds
    assert "tool_result" in kinds
    assert "usage" in kinds
    assert kinds[-1] == "final"

    tool_result = next(event for event in events if event.kind == "tool_result")
    assert tool_result.data["result"] == "TOKYO"
    assert stream.error is None
    assert stream.usage == {"total_tokens": 12}


def test_stream_events_merges_tool_deltas_without_id_or_index(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(
        iter([
            make_chunk(tool_calls=[make_tool_call("echo", '{"text":"to', call_id="call_1")]),
            make_chunk(
                tool_calls=[
                    SimpleNamespace(
                        type="function",
                        function=SimpleNamespace(name="", arguments='kyo"}'),
                    )
                ],
                usage={"total_tokens": 9},
            ),
        ])
    )

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")
    stream = llm.stream_events("Call echo for tokyo", tools=[echo])
    events = list(stream)

    tool_calls = [event for event in events if event.kind == "tool_call"]
    assert len(tool_calls) == 1
    assert tool_calls[0].data["call"]["function"]["name"] == "echo"
    assert tool_calls[0].data["call"]["function"]["arguments"] == '{"text":"tokyo"}'

    tool_results = [event for event in events if event.kind == "tool_result"]
    assert len(tool_results) == 1
    assert tool_results[0].data["result"] == "TOKYO"
    assert stream.error is None
    assert stream.usage == {"total_tokens": 9}


def test_responses_mode_chat_and_run_tools(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openrouter")
    client.queue_responses(
        make_responses_response(text="ready"),
        make_responses_response(tool_calls=[make_responses_tool_call("echo", '{"text":"tokyo"}', call_id="call_r1")]),
    )

    llm = LLM(model="openrouter:openrouter/free", api_key="dummy", api_mode="responses")
    out = llm.chat("Reply with ready")
    result = llm.run_tools("Call echo for tokyo", tools=[echo])

    assert out == "ready"
    assert result.kind == "tools"
    assert result.tool_results == ["TOKYO"]
    assert result.error is None
    assert client.calls[0]["input_data"] == [{"role": "user", "content": "Reply with ready"}]
    assert client.calls[1]["tools"][0]["type"] == "function"
    assert client.calls[1]["tools"][0]["name"] == "echo"
    assert client.calls[1]["tools"][0]["description"] == ""
    assert client.calls[1]["tools"][0]["parameters"]["required"] == ["text"]
    assert client.calls[1]["tools"][0]["parameters"]["properties"]["text"]["type"] == "string"


def test_responses_mode_accepts_dict_response_shape(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openrouter")
    client.queue_responses({
        "output_text": "",
        "output": [
            {
                "type": "function_call",
                "name": "echo",
                "arguments": '{"text":"tokyo"}',
                "call_id": "call_dict_1",
            }
        ],
        "usage": {"total_tokens": 5},
    })

    llm = LLM(model="openrouter:openrouter/free", api_key="dummy", api_mode="responses")
    result = llm.run_tools("Call echo for tokyo", tools=[echo])

    assert result.kind == "tools"
    assert result.tool_results == ["TOKYO"]
    assert result.error is None


def test_stream_events_supports_responses_events_shape(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openrouter")
    client.queue_responses(
        iter([
            make_responses_text_delta("Checking "),
            make_responses_function_delta('{"text":"to', item_id="call_rsp_1"),
            make_responses_function_delta('kyo"}', item_id="call_rsp_1"),
            make_responses_function_done("echo", '{"text":"tokyo"}', item_id="call_rsp_1"),
            make_responses_completed({"total_tokens": 12}),
        ])
    )

    llm = LLM(model="openrouter:openrouter/free", api_key="dummy", api_mode="responses")
    stream = llm.stream_events("Call echo for tokyo", tools=[echo])
    events = list(stream)

    kinds = [event.kind for event in events]
    assert "text" in kinds
    assert "tool_call" in kinds
    assert "tool_result" in kinds
    assert "usage" in kinds
    assert kinds[-1] == "final"

    tool_calls = [event for event in events if event.kind == "tool_call"]
    assert len(tool_calls) == 1
    assert tool_calls[0].data["call"]["function"]["name"] == "echo"
    assert tool_calls[0].data["call"]["function"]["arguments"] == '{"text":"tokyo"}'

    tool_results = [event for event in events if event.kind == "tool_result"]
    assert len(tool_results) == 1
    assert tool_results[0].data["result"] == "TOKYO"
    assert stream.error is None
    assert stream.usage == {"total_tokens": 12}


def test_stream_supports_responses_text_deltas(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openrouter")
    client.queue_responses(
        iter([
            make_responses_text_delta("Hello"),
            make_responses_text_delta(" world"),
            make_responses_completed({"total_tokens": 7}),
        ])
    )

    llm = LLM(model="openrouter:openrouter/free", api_key="dummy", api_mode="responses")
    stream = llm.stream("Say hello")
    text = "".join(list(stream))

    assert text == "Hello world"
    assert stream.error is None
    assert stream.usage == {"total_tokens": 7}


@pytest.mark.asyncio
async def test_run_tools_async_executes_async_tool_handler(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(make_response(tool_calls=[make_tool_call("async_echo", '{"text":"tokyo"}')]))

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")
    result = await llm.run_tools_async("Call async echo for tokyo", tools=[async_echo])

    assert result.kind == "tools"
    assert result.tool_results == ["TOKYO"]
    assert result.error is None


@pytest.mark.asyncio
async def test_responses_mode_async_chat_tool_calls_and_stream(fake_anyllm) -> None:
    async def _astream() -> object:
        for item in [
            make_responses_text_delta("Hello"),
            make_responses_text_delta(" async"),
            make_responses_completed({"total_tokens": 9}),
        ]:
            yield item

    client = fake_anyllm.ensure("openrouter")
    client.queue_aresponses(
        make_responses_response(text="pong"),
        make_responses_response(tool_calls=[make_responses_tool_call("echo", '{"text":"tokyo"}', call_id="call_a1")]),
        _astream(),
    )

    llm = LLM(model="openrouter:openrouter/free", api_key="dummy", api_mode="responses")

    text = await llm.chat_async("Reply with pong")
    calls = await llm.tool_calls_async("Use echo for tokyo", tools=[echo])
    stream = await llm.stream_async("Say hello async")
    streamed = "".join([chunk async for chunk in stream])

    assert text == "pong"
    assert len(calls) == 1
    assert calls[0]["function"]["name"] == "echo"
    assert calls[0]["function"]["arguments"] == '{"text":"tokyo"}'
    assert streamed == "Hello async"
    assert stream.error is None
    assert stream.usage == {"total_tokens": 9}


@pytest.mark.asyncio
async def test_stream_events_async_executes_async_tool_handler(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(make_response(tool_calls=[make_tool_call("async_echo", '{"text":"tokyo"}')]))

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")
    stream = await llm.stream_events_async("Call async echo for tokyo", tools=[async_echo])
    events = [event async for event in stream]
    tool_results = [event for event in events if event.kind == "tool_result"]

    assert len(tool_results) == 1
    assert tool_results[0].data["result"] == "TOKYO"
    assert stream.error is None


def test_text_shortcuts_and_embeddings_share_the_same_facade(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_completion(
        make_response(tool_calls=[make_tool_call("if_decision", '{"value": true}')]),
        make_response(tool_calls=[make_tool_call("classify_decision", '{"label": "support"}')]),
        make_response(tool_calls=[make_tool_call("classify_decision", '{"label": "other"}')]),
    )
    client.queue_embedding({"data": [{"embedding": [0.1, 0.2, 0.3]}]})

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy")

    decision = llm.if_("The service is down", "Should we page on-call?")
    assert decision is True

    label = llm.classify("Need invoice support", ["support", "sales"])
    assert label == "support"

    with pytest.raises(ErrorPayload) as exc_info:
        llm.classify("Unknown intent", ["support", "sales"])
    assert exc_info.value.kind == ErrorKind.INVALID_INPUT

    embedding = llm.embed("incident summary")
    assert embedding == {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
