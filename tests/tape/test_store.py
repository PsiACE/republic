from __future__ import annotations

from republic import LLM


class TestTapeStore:
    def test_custom_tape_store_is_used(self, stub_client, recording_tape_store):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", tape_store=recording_tape_store)
        tape = llm.tape("conv")

        assert tape.create("Hi") == "Hello"
        assert recording_tape_store.appended

    def test_appends_in_order(self, stub_client, recording_tape_store):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", tape_store=recording_tape_store)
        tape = llm.tape("conv")

        tape.create("Hi", system_prompt="sys")
        assert [entry.payload["role"] for _, entry in recording_tape_store.appended] == [
            "user",
            "assistant",
        ]

    def test_system_prompt_not_appended(self, stub_client, recording_tape_store):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", tape_store=recording_tape_store)
        tape = llm.tape("conv")

        tape.create("Hi", system_prompt="sys")
        assert [entry.payload["role"] for _, entry in recording_tape_store.appended] == [
            "user",
            "assistant",
        ]

    def test_handoff_appends_anchor(self, recording_tape_store):
        llm = LLM(model="openai:gpt-4o-mini", tape_store=recording_tape_store)
        tape = llm.tape("conv")

        entries = tape.handoff("handoff:v1", state={"phase": "summary"})
        assert entries
        assert entries[0].kind == "anchor"
        assert entries[0].payload["name"] == "handoff:v1"
        assert entries[0].payload["state"]["phase"] == "summary"
