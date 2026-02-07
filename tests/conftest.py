from __future__ import annotations

import os
from pathlib import Path

import pytest


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        if key:
            env[key] = value
    return env


def _apply_env(env: dict[str, str]) -> None:
    for key, value in env.items():
        os.environ.setdefault(key, value)
    if "OPENROUTER_API_KEY" not in os.environ and "LLM_API_KEY" in os.environ:
        os.environ["OPENROUTER_API_KEY"] = os.environ["LLM_API_KEY"]


_apply_env(_load_env_file(Path(".env")))


@pytest.fixture(scope="session")
def openrouter_api_key() -> str:
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("LLM_API_KEY is not set.")
    assert key is not None
    return key


@pytest.fixture(scope="session")
def openrouter_chat_model() -> str:
    return os.getenv("REPUBLIC_CHAT_MODEL", "openrouter:openrouter/free")


@pytest.fixture(scope="session")
def openrouter_stream_model() -> str:
    return os.getenv("REPUBLIC_STREAM_MODEL", "openrouter:openai/gpt-4o-mini")


@pytest.fixture(scope="session")
def openrouter_embedding_model() -> str:
    return os.getenv("REPUBLIC_EMBEDDING_MODEL", "openrouter:openai/text-embedding-3-small")


@pytest.fixture(scope="session")
def openrouter_tool_model() -> str:
    return os.getenv("REPUBLIC_TOOL_MODEL", "openrouter:openai/gpt-4o-mini")
