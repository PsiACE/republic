from __future__ import annotations

from republic import LLM


class TestBatch:
    def test_create_uses_client(self, stub_client):
        expected = object()
        stub_client.create_batch.return_value = expected
        llm = LLM(model="openai:gpt-4o-mini")

        assert (
            llm.batch.create(
                input_file_path="/tmp/input.jsonl",
                endpoint="/v1/chat/completions",
            )
            is expected
        )
