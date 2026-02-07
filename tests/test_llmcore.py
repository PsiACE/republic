from __future__ import annotations

import pytest

from republic.core.errors import ErrorKind, RepublicError
from republic.core.execution import LLMCore


def test_resolve_model_provider_with_prefix() -> None:
    provider, model = LLMCore.resolve_model_provider("openrouter:openrouter/free", None)
    assert provider == "openrouter"
    assert model == "openrouter/free"


def test_resolve_model_provider_with_explicit_provider() -> None:
    provider, model = LLMCore.resolve_model_provider("gpt-4o-mini", "openai")
    assert provider == "openai"
    assert model == "gpt-4o-mini"


def test_resolve_model_provider_rejects_mixed() -> None:
    with pytest.raises(RepublicError) as exc:
        LLMCore.resolve_model_provider("openai:gpt-4o-mini", "openai")
    assert exc.value.kind == ErrorKind.INVALID_INPUT


def test_resolve_fallback_requires_provider() -> None:
    core = LLMCore(
        provider="openrouter",
        model="openrouter/free",
        fallback_models=[],
        max_retries=1,
        api_key=None,
        api_base=None,
        client_args={},
        verbose=0,
    )
    provider, model = core.resolve_fallback("openrouter/free")
    assert provider == "openrouter"
    assert model == "openrouter/free"
