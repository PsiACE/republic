from __future__ import annotations

from republic import LLM
from republic.clients.chat import ChatClient

from .fakes import make_responses_function_call, make_responses_response


def test_llm_use_responses_calls_responses(fake_anyllm) -> None:
    client = fake_anyllm.ensure("openai")
    client.queue_responses(make_responses_response(text="hello"))

    llm = LLM(model="openai:gpt-4o-mini", api_key="dummy", use_responses=True)
    result = llm.chat("hi")

    assert result == "hello"
    assert client.calls[-1].get("responses") is True
    assert client.calls[-1]["input_data"][0]["role"] == "user"


def test_extract_tool_calls_from_responses() -> None:
    response = make_responses_response(
        tool_calls=[make_responses_function_call("echo", '{"text":"hi"}')]
    )

    calls = ChatClient._extract_tool_calls(response)

    assert calls == [
        {
            "function": {"name": "echo", "arguments": '{"text":"hi"}'},
            "id": "call_1",
            "type": "function",
        }
    ]
