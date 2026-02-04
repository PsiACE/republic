from __future__ import annotations

import pytest

from republic import LLM, ErrorKind, RepublicError


class TestTextHelpers:
    def test_if_returns_boolean(self, stub_client):
        stub_client.completion.return_value = "Yes"
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.text.if_("Hello", "Is this a greeting?") is True

    def test_classify_matches_choice(self, stub_client):
        stub_client.completion.return_value = "alpha"
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.text.classify("message", ["alpha", "beta"]) == "alpha"

    def test_classify_defaults_when_unknown(self, stub_client):
        stub_client.completion.return_value = "unknown"
        llm = LLM(model="openai:gpt-4o-mini")

        assert llm.text.classify("message", ["alpha", "beta"]) == "alpha"

    def test_classify_rejects_empty_choices(self):
        llm = LLM(model="openai:gpt-4o-mini")

        with pytest.raises(RepublicError) as exc_info:
            llm.text.classify("message", [])
        assert exc_info.value.kind == ErrorKind.INVALID_INPUT
