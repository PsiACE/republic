from __future__ import annotations

import builtins

import pytest

from republic import TapeEntry


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


@pytest.fixture
def stub_client(monkeypatch):
    client = StubClient()
    monkeypatch.setattr("republic.core.execution.AnyLLM.create", lambda *args, **kwargs: client)
    return client


class RecordingTapeStore:
    def __init__(self, initial_tapes: dict[str, builtins.list[TapeEntry]] | None = None) -> None:
        self.appended: list[tuple[str, TapeEntry]] = []
        self._tapes: dict[str, list[TapeEntry]] = {
            name: [entry.copy() for entry in entries] for name, entries in (initial_tapes or {}).items()
        }

    def seed(self, name: str, entries: builtins.list[TapeEntry]) -> None:
        self._tapes[name] = [entry.copy() for entry in entries]

    def list_tapes(self) -> builtins.list[str]:
        return sorted(self._tapes.keys())

    def reset(self, name: str) -> None:
        self._tapes.pop(name, None)

    def read(self, name: str):
        entries = self._tapes.get(name)
        if entries is None:
            return None
        return [entry.copy() for entry in entries]

    def append(self, name: str, entry: TapeEntry) -> None:
        self.appended.append((name, entry.copy()))
        self._tapes.setdefault(name, []).append(entry.copy())


@pytest.fixture
def recording_tape_store() -> RecordingTapeStore:
    return RecordingTapeStore()
