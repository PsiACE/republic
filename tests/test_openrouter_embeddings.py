from __future__ import annotations

from republic import LLM


def test_openrouter_embeddings(openrouter_api_key: str, openrouter_embedding_model: str) -> None:
    llm = LLM(model=openrouter_embedding_model, api_key=openrouter_api_key)
    result = llm.embed(["hello", "world"])
    assert result.error is None
    assert result.value is not None
