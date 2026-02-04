from __future__ import annotations

from republic import LLM


class TestConversationStore:
    def test_custom_conversation_store_is_used(self, stub_client, recording_store):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", conversation_store=recording_store)

        assert llm.chat.create("Hi", conversation="conv") == "Hello"
        assert recording_store.appended

    def test_appends_in_order(self, stub_client, recording_store):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", conversation_store=recording_store)

        llm.chat.create("Hi", conversation="conv", system_prompt="sys")
        assert [msg["role"] for _, msg in recording_store.appended] == ["system", "user", "assistant"]

    def test_system_prompt_not_duplicated(self, stub_client, recording_store):
        recording_store.seed("conv", [{"role": "system", "content": "sys"}])
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", conversation_store=recording_store)

        llm.chat.create("Hi", conversation="conv", system_prompt="sys")
        assert [msg["role"] for _, msg in recording_store.appended] == ["user", "assistant"]
