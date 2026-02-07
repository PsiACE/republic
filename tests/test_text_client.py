from __future__ import annotations

import asyncio

from republic.clients.text import TextClient
from republic.core.errors import ErrorKind
from republic.core.results import StructuredOutput


class _DummyChat:
    def __init__(self, response: StructuredOutput) -> None:
        self._response = response

    def tool_calls(self, *args, **kwargs) -> StructuredOutput:
        return self._response

    async def tool_calls_async(self, *args, **kwargs) -> StructuredOutput:
        await asyncio.sleep(0)
        return self._response


def test_if_parsing() -> None:
    response = StructuredOutput([{"function": {"arguments": {"value": True}}}], None)
    client = TextClient(_DummyChat(response))
    result = client.if_("hi", "is this positive?")
    assert result.value is True
    assert result.error is None


def test_classify_validation() -> None:
    response = StructuredOutput([{"function": {"arguments": {"label": "other"}}}], None)
    client = TextClient(_DummyChat(response))
    result = client.classify("text", ["yes", "no"])
    assert result.error is not None
    assert result.error.kind == ErrorKind.INVALID_INPUT


def test_async_if_parsing() -> None:
    response = StructuredOutput([{"function": {"arguments": {"value": False}}}], None)
    client = TextClient(_DummyChat(response))
    result = asyncio.run(client.if_async("hi", "is this negative?"))
    assert result.value is False
    assert result.error is None
