from __future__ import annotations

import re
import warnings

import pytest
from any_llm.exceptions import AnyLLMError, ProviderError

from republic import LLM, TapeContext, TapeEntry
from republic.__about__ import DEFAULT_MODEL
from republic.core import ErrorKind, RepublicError
from republic.tape import InMemoryTapeStore


class TestDefaults:
    def test_default_model_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            llm = LLM()
            assert llm.provider == DEFAULT_MODEL.split(":", 1)[0]
            assert llm.model == DEFAULT_MODEL.split(":", 1)[1]
            assert any(re.search(f"defaulting to {DEFAULT_MODEL}", str(w.message)) for w in caught)


class TestRetries:
    def test_max_retries_zero_still_attempts(self, stub_client):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini", max_retries=0)

        assert llm.chat.create("Hi") == "Hello"

    def test_max_retries_negative_rejected(self):
        with pytest.raises(RepublicError) as exc_info:
            LLM(model="openai:gpt-4o-mini", max_retries=-1)
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT


class TestFallback:
    def test_fallback_returns_success(self, stub_client):
        stub_client.completion.side_effect = [ProviderError(), "Fallback ok"]
        llm = LLM(model="openai:gpt-4o-mini", fallback_models=["openai:gpt-4.1-mini"], max_retries=1)

        assert llm.chat.create("Hi") == "Fallback ok"

    def test_non_retryable_provider_error_does_not_fallback(self, stub_client):
        stub_client.completion.side_effect = [AnyLLMError("boom"), "Fallback ok"]
        llm = LLM(model="openai:gpt-4o-mini", fallback_models=["openai:gpt-4.1-mini"], max_retries=2)

        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create("Hi")
        assert exc_info.value.kind == ErrorKind.PROVIDER


class TestValidation:
    def test_requires_provider_colon_format(self):
        with pytest.raises(RepublicError, match="provider:model"):
            LLM(model="openai/gpt-4o-mini")


class TestErrorClassification:
    def test_custom_error_classifier_is_used(self, stub_client):
        stub_client.completion.side_effect = ProviderError()

        def classify(exc: Exception):
            return ErrorKind.INVALID_INPUT

        llm = LLM(model="openai:gpt-4o-mini", max_retries=1, error_classifier=classify)

        with pytest.raises(RepublicError) as exc_info:
            llm.chat.create("Hi")
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT


class TestTapeHandles:
    def test_tape_list_exposes_names(self, stub_client):
        stub_client.completion.return_value = "Hello"
        llm = LLM(model="openai:gpt-4o-mini")
        tape = llm.tape("notes")

        tape.create("Hi")
        assert llm.tapes() == ["notes"]

    def test_context_property_sets_default(self, stub_client):
        stub_client.completion.return_value = "Hello"
        store = InMemoryTapeStore()
        store.append("notes", TapeEntry.message({"role": "user", "content": "old"}))
        store.append("notes", TapeEntry.anchor("handoff"))
        llm = LLM(model="openai:gpt-4o-mini", tape_store=store)
        llm.context = TapeContext(anchor=None)

        tape = llm.tape("notes")
        tape.create("Hi")
        messages = stub_client.completion.calls[0][1]["messages"]
        assert {"role": "user", "content": "old"} in messages
