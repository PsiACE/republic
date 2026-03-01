"""Tape stores for Republic."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, NoReturn, Protocol, TypeGuard

from republic.core.errors import ErrorKind
from republic.core.results import ErrorPayload
from republic.tape.entries import TapeEntry

if TYPE_CHECKING:
    from republic.tape.query import TapeQuery


class TapeStore(Protocol):
    """Append-only tape storage interface."""

    def list_tapes(self) -> list[str]: ...

    def reset(self, tape: str) -> None: ...

    def fetch_all(self, query: TapeQuery) -> Iterable[TapeEntry]: ...

    def append(self, tape: str, entry: TapeEntry) -> None: ...


class AsyncTapeStore(Protocol):
    """Async append-only tape storage interface."""

    async def list_tapes(self) -> list[str]: ...

    async def reset(self, tape: str) -> None: ...

    async def fetch_all(self, query: TapeQuery) -> Iterable[TapeEntry]: ...

    async def append(self, tape: str, entry: TapeEntry) -> None: ...


def is_async_tape_store(store: TapeStore | AsyncTapeStore) -> TypeGuard[AsyncTapeStore]:
    return hasattr(store, "append") and inspect.iscoroutinefunction(store.append)


def _anchor_index(
    entries: Sequence[TapeEntry],
    name: str | None,
    *,
    default: int,
    forward: bool,
    start: int = 0,
) -> int:
    rng = range(start, len(entries)) if forward else range(len(entries) - 1, start - 1, -1)
    for idx in rng:
        entry = entries[idx]
        if entry.kind != "anchor":
            continue
        if name is not None and entry.payload.get("name") != name:
            continue
        return idx
    return default


class InMemoryQueryMixin:
    """Mixin to implement query() in-memory for simple stores."""

    def read(self, tape: str) -> list[TapeEntry] | None:
        raise NotImplementedError("InMemoryQueryMixin requires a read() method to be implemented.")

    def fetch_all(self, query: TapeQuery) -> Iterable[TapeEntry]:
        entries = self.read(query.tape) or []
        start_index = 0
        end_index: int | None = None

        if query._between is not None:
            start_name, end_name = query._between
            start_idx = _anchor_index(entries, start_name, default=-1, forward=False)
            if start_idx < 0:
                raise ErrorPayload(ErrorKind.NOT_FOUND, f"Anchor '{start_name}' was not found.")
            end_idx = _anchor_index(entries, end_name, default=-1, forward=True, start=start_idx + 1)
            if end_idx < 0:
                raise ErrorPayload(ErrorKind.NOT_FOUND, f"Anchor '{end_name}' was not found.")
            start_index = min(start_idx + 1, len(entries))
            end_index = min(max(start_index, end_idx), len(entries))
        elif query._after_last:
            anchor_index = _anchor_index(entries, None, default=-1, forward=False)
            if anchor_index < 0:
                raise ErrorPayload(ErrorKind.NOT_FOUND, "No anchors found in tape.")
            start_index = min(anchor_index + 1, len(entries))
        elif query._after_anchor is not None:
            anchor_index = _anchor_index(entries, query._after_anchor, default=-1, forward=False)
            if anchor_index < 0:
                raise ErrorPayload(ErrorKind.NOT_FOUND, f"Anchor '{query._after_anchor}' was not found.")
            start_index = min(anchor_index + 1, len(entries))

        sliced = entries[start_index:end_index]
        if query._kinds:
            sliced = [entry for entry in sliced if entry.kind in query._kinds]
        if query._limit is not None:
            sliced = sliced[: query._limit]
        return sliced


class InMemoryTapeStore(InMemoryQueryMixin):
    """In-memory tape storage (not thread-safe)."""

    def __init__(self) -> None:
        self._tapes: dict[str, list[TapeEntry]] = {}
        self._next_id: dict[str, int] = {}

    def list_tapes(self) -> list[str]:
        return sorted(self._tapes.keys())

    def reset(self, tape: str) -> None:
        self._tapes.pop(tape, None)
        self._next_id.pop(tape, None)

    def read(self, tape: str) -> list[TapeEntry] | None:
        entries = self._tapes.get(tape)
        if entries is None:
            return None
        return [entry.copy() for entry in entries]

    def append(self, tape: str, entry: TapeEntry) -> None:
        next_id = self._next_id.get(tape, 1)
        self._next_id[tape] = next_id + 1
        stored = TapeEntry(next_id, entry.kind, dict(entry.payload), dict(entry.meta))
        self._tapes.setdefault(tape, []).append(stored)


class AsyncTapeStoreAdapter:
    """Adapt a sync TapeStore to AsyncTapeStore."""

    def __init__(self, store: TapeStore) -> None:
        self._store = store

    async def list_tapes(self) -> list[str]:
        return await asyncio.to_thread(self._store.list_tapes)

    async def reset(self, tape: str) -> None:
        await asyncio.to_thread(self._store.reset, tape)

    async def fetch_all(self, query: TapeQuery) -> Iterable[TapeEntry]:
        return await asyncio.to_thread(self._store.fetch_all, query)

    async def append(self, tape: str, entry: TapeEntry) -> None:
        await asyncio.to_thread(self._store.append, tape, entry)


class UnavailableTapeStore:
    """Sync TapeStore sentinel that always fails with a clear message."""

    def __init__(self, message: str) -> None:
        self._message = message

    def _raise(self) -> NoReturn:
        raise ErrorPayload(ErrorKind.INVALID_INPUT, self._message)

    def list_tapes(self) -> list[str]:
        self._raise()

    def reset(self, tape: str) -> None:
        self._raise()

    def fetch_all(self, query: TapeQuery) -> Iterable[TapeEntry]:
        self._raise()

    def append(self, tape: str, entry: TapeEntry) -> None:
        self._raise()
