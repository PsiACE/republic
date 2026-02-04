"""Conversation storage for Republic."""

from __future__ import annotations

import builtins
from typing import Any, Protocol


class ConversationStore(Protocol):
    """Conversation storage interface."""

    def list(self) -> builtins.list[str]: ...

    def reset(self, name: str) -> None: ...

    def get(self, name: str) -> builtins.list[dict[str, Any]] | None: ...

    def append(self, name: str, message: dict[str, Any]) -> None: ...


class InMemoryConversationStore:
    """In-memory conversation storage (not thread-safe)."""

    def __init__(self) -> None:
        self._conversations: dict[str, list[dict[str, Any]]] = {}

    def list(self) -> builtins.list[str]:
        return sorted(self._conversations.keys())

    def reset(self, name: str) -> None:
        self._conversations.pop(name, None)

    def get(self, name: str) -> builtins.list[dict[str, Any]] | None:
        history = self._conversations.get(name)
        if history is None:
            return None
        return [dict(message) for message in history]

    def append(self, name: str, message: dict[str, Any]) -> None:
        self._conversations.setdefault(name, []).append(message)
