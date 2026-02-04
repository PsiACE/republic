"""Conversation storage for Republic."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


class ConversationStore(Protocol):
    """Conversation storage interface."""

    def list(self) -> List[str]:
        ...

    def reset(self, name: str) -> None:
        ...

    def get(self, name: str) -> Optional[List[Dict[str, Any]]]:
        ...

    def append(self, name: str, message: Dict[str, Any]) -> None:
        ...


class InMemoryConversationStore:
    """In-memory conversation storage (not thread-safe)."""

    def __init__(self) -> None:
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}

    def list(self) -> List[str]:
        return sorted(self._conversations.keys())

    def reset(self, name: str) -> None:
        self._conversations.pop(name, None)

    def get(self, name: str) -> Optional[List[Dict[str, Any]]]:
        history = self._conversations.get(name)
        if history is None:
            return None
        return [dict(message) for message in history]

    def append(self, name: str, message: Dict[str, Any]) -> None:
        self._conversations.setdefault(name, []).append(message)
