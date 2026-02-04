from __future__ import annotations

from typing import Dict, List, Tuple

import pytest


@pytest.fixture
def stub_client(monkeypatch):
    class StubCallable:
        def __init__(self) -> None:
            self.return_value = None
            self.side_effect = None
            self.calls = []

        def _next_effect(self):
            if isinstance(self.side_effect, list):
                if not self.side_effect:
                    return None
                return self.side_effect.pop(0)
            return self.side_effect

        def __call__(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            if self.side_effect is not None:
                effect = self._next_effect()
                if isinstance(effect, Exception):
                    raise effect
                if callable(effect):
                    return effect(*args, **kwargs)
                return effect
            return self.return_value

    class AsyncStubCallable(StubCallable):
        async def __call__(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            if self.side_effect is not None:
                effect = self._next_effect()
                if isinstance(effect, Exception):
                    raise effect
                if callable(effect):
                    result = effect(*args, **kwargs)
                    return result
                return effect
            return self.return_value

    class StubClient:
        def __init__(self) -> None:
            self.completion = StubCallable()
            self.acompletion = AsyncStubCallable()
            self.responses = StubCallable()
            self.aresponses = AsyncStubCallable()
            self._embedding = StubCallable()
            self.aembedding = AsyncStubCallable()
            self.list_models = StubCallable()
            self.alist_models = AsyncStubCallable()
            self.create_batch = StubCallable()
            self.acreate_batch = AsyncStubCallable()
            self.retrieve_batch = StubCallable()
            self.aretrieve_batch = AsyncStubCallable()
            self.cancel_batch = StubCallable()
            self.acancel_batch = AsyncStubCallable()
            self.list_batches = StubCallable()
            self.alist_batches = AsyncStubCallable()

    client = StubClient()
    monkeypatch.setattr("republic.core.execution.AnyLLM.create", lambda *args, **kwargs: client)
    return client


class RecordingConversationStore:
    def __init__(self, initial_history: Dict[str, List[dict]] | None = None) -> None:
        self.appended: List[Tuple[str, dict]] = []
        self._history: Dict[str, List[dict]] = {
            name: [dict(message) for message in messages]
            for name, messages in (initial_history or {}).items()
        }

    def seed(self, name: str, messages: List[dict]) -> None:
        self._history[name] = [dict(message) for message in messages]

    def list(self) -> List[str]:
        return sorted(self._history.keys())

    def reset(self, name: str) -> None:
        self._history.pop(name, None)

    def get(self, name: str):
        history = self._history.get(name)
        if history is None:
            return None
        return [dict(message) for message in history]

    def append(self, name: str, message: dict) -> None:
        self.appended.append((name, message))
        self._history.setdefault(name, []).append(dict(message))


@pytest.fixture
def recording_store() -> RecordingConversationStore:
    return RecordingConversationStore()
