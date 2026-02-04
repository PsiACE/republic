from __future__ import annotations

from pydantic import BaseModel

from republic import LLM, ToolSet, schema_from_model


class TestResponses:
    def test_create_uses_client(self, stub_client):
        expected = object()
        stub_client.responses.return_value = expected
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.responses.create("Hi") is expected

    def test_stream_uses_client(self, stub_client):
        expected = iter(["event"])
        stub_client.responses.return_value = expected
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.responses.stream("Hi") is expected

    def test_accepts_toolset(self, stub_client):
        class Weather(BaseModel):
            location: str

        tool_schema = schema_from_model(Weather)
        toolset = ToolSet.from_tools([tool_schema])

        stub_client.responses.return_value = object()
        llm = LLM(model="openai:gpt-4o-mini")
        llm.responses.create("Hi", tools=toolset)

        _, kwargs = stub_client.responses.calls[-1]
        assert kwargs["tools"] == [tool_schema]
