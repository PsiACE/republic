from __future__ import annotations

from republic import LLM, TapeContext, TapeEntry
from republic.tape import InMemoryTapeStore


class TestTapeContext:
    def test_context_defaults_to_last_anchor(self, stub_client):
        stub_client.completion.return_value = "Hello"
        store = InMemoryTapeStore()
        store.append("conv", TapeEntry.message({"role": "user", "content": "old"}))
        store.append("conv", TapeEntry.anchor("handoff"))
        llm = LLM(
            model="openai:gpt-4o-mini",
            tape_store=store,
        )
        tape = llm.tape("conv")

        tape.create("Hi")
        messages = stub_client.completion.calls[0][1]["messages"]
        assert {"role": "user", "content": "old"} not in messages
        assert messages[-1]["content"] == "Hi"

    def test_context_uses_named_anchor(self, stub_client):
        stub_client.completion.return_value = "Hello"
        store = InMemoryTapeStore()
        store.append("conv", TapeEntry.message({"role": "user", "content": "old"}))
        store.append("conv", TapeEntry.anchor("handoff"))
        llm = LLM(
            model="openai:gpt-4o-mini",
            tape_store=store,
            context=TapeContext(anchor="handoff"),
        )
        tape = llm.tape("conv")

        tape.create("Hi")
        messages = stub_client.completion.calls[0][1]["messages"]
        assert {"role": "user", "content": "old"} not in messages
        assert messages[-1]["content"] == "Hi"

    def test_context_selector_filters_entries(self, stub_client):
        stub_client.completion.return_value = "Hello"
        store = InMemoryTapeStore()
        store.append("conv", TapeEntry.message({"role": "user", "content": "first"}))
        store.append("conv", TapeEntry.message({"role": "user", "content": "second"}))

        def select(entries, context):
            return [entries[-1].payload]

        llm = LLM(
            model="openai:gpt-4o-mini",
            tape_store=store,
            context=TapeContext(anchor=None, select=select),
        )
        tape = llm.tape("conv")

        tape.create("Hi")
        messages = stub_client.completion.calls[0][1]["messages"]
        assert {"role": "user", "content": "first"} not in messages
        assert {"role": "user", "content": "second"} in messages

    def test_context_selector_supports_anchor_strategy(self, stub_client):
        stub_client.completion.return_value = "Hello"
        store = InMemoryTapeStore()
        store.append("conv", TapeEntry.message({"role": "user", "content": "old"}))
        store.append("conv", TapeEntry.anchor("phase:execute"))
        store.append("conv", TapeEntry.message({"role": "user", "content": "run"}))
        store.append("conv", TapeEntry.anchor("handoff:summary", state={"text": "Summary block"}))
        store.append("conv", TapeEntry.message({"role": "user", "content": "ignored"}))

        def select(entries, context):
            start = 0
            end = len(entries)
            summary_text = None
            for idx, entry in enumerate(entries):
                if entry.kind != "anchor":
                    continue
                anchor_name = entry.payload.get("name")
                if anchor_name == "phase:execute":
                    start = idx + 1
                if anchor_name == "handoff:summary":
                    end = idx
                    summary_text = entry.payload.get("state", {}).get("text")
                    break

            segment = entries[start:end]
            messages = [entry.payload for entry in segment if entry.kind == "message"]
            if summary_text:
                messages.insert(0, {"role": "system", "content": summary_text})
            return messages

        llm = LLM(
            model="openai:gpt-4o-mini",
            tape_store=store,
            context=TapeContext(anchor=None, select=select),
        )
        tape = llm.tape("conv")

        tape.create("Hi")
        messages = stub_client.completion.calls[0][1]["messages"]
        assert {"role": "user", "content": "old"} not in messages
        assert {"role": "user", "content": "ignored"} not in messages
        assert {"role": "system", "content": "Summary block"} in messages
        assert {"role": "user", "content": "run"} in messages
        assert messages[-1]["content"] == "Hi"

    def test_missing_anchor_is_noop(self, stub_client):
        stub_client.completion.return_value = "Hello"
        store = InMemoryTapeStore()
        store.append("conv", TapeEntry.message({"role": "user", "content": "old"}))
        llm = LLM(
            model="openai:gpt-4o-mini",
            tape_store=store,
            context=TapeContext(anchor="missing"),
        )
        tape = llm.tape("conv")

        tape.create("Hi")
        messages = stub_client.completion.calls[0][1]["messages"]
        assert {"role": "user", "content": "old"} in messages
        assert messages[-1]["content"] == "Hi"
