from __future__ import annotations

from republic import LLM, tool


def test_openrouter_chat_create(openrouter_api_key: str, openrouter_chat_model: str) -> None:
    llm = LLM(model=openrouter_chat_model, api_key=openrouter_api_key)
    result = llm.chat.create("Say hello in one word.", max_tokens=16)
    assert result.error is None
    assert isinstance(result.value, str)
    assert result.value.strip()


def test_openrouter_stream(openrouter_api_key: str, openrouter_stream_model: str) -> None:
    llm = LLM(model=openrouter_stream_model, api_key=openrouter_api_key)
    stream = llm.stream("Reply with two short words.", max_tokens=16)
    text = "".join(chunk for chunk in stream)
    assert stream.error is None
    assert text.strip()


def test_openrouter_stream_events(openrouter_api_key: str, openrouter_stream_model: str) -> None:
    llm = LLM(model=openrouter_stream_model, api_key=openrouter_api_key)
    events = list(llm.stream_events("Say hi.", max_tokens=16))
    assert events
    assert events[-1].kind == "final"


def test_openrouter_tools_auto(openrouter_api_key: str, openrouter_tool_model: str) -> None:
    llm = LLM(model=openrouter_tool_model, api_key=openrouter_api_key)

    @tool
    def echo(text: str) -> str:
        return text

    result = llm.chat.tools_auto("Call the echo tool with 'hi'.", tools=[echo], max_tokens=32)
    assert result.error is None
    assert result.kind in {"text", "tools"}
