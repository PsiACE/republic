"""Query helpers for tape entries."""

from __future__ import annotations

from collections.abc import Coroutine, Iterable
from dataclasses import dataclass, field, replace
from typing import Generic, Self, TypeVar, overload

from republic.tape.entries import TapeEntry
from republic.tape.store import AsyncTapeStore, TapeStore

T = TypeVar("T", TapeStore, AsyncTapeStore)


@dataclass(frozen=True)
class TapeQuery(Generic[T]):
    tape: str
    store: T
    _after_anchor: str | None = None
    _after_last: bool = False
    _between: tuple[str, str] | None = None
    _kinds: tuple[str, ...] = field(default_factory=tuple)
    _limit: int | None = None

    def after_anchor(self, name: str) -> Self:
        if not name:
            return replace(self, _after_anchor=None, _after_last=False)
        return replace(self, _after_anchor=name, _after_last=False)

    def last_anchor(self) -> Self:
        return replace(self, _after_anchor=None, _after_last=True)

    def between_anchors(self, start: str, end: str) -> Self:
        return replace(self, _between=(start, end))

    def kinds(self, *kinds: str) -> Self:
        return replace(self, _kinds=kinds)

    def limit(self, value: int) -> Self:
        return replace(self, _limit=value)

    @overload
    def all(self: TapeQuery[TapeStore]) -> Iterable[TapeEntry]: ...

    @overload
    async def all(self: TapeQuery[AsyncTapeStore]) -> Iterable[TapeEntry]: ...

    def all(self) -> Iterable[TapeEntry] | Coroutine[None, None, Iterable[TapeEntry]]:
        return self.store.fetch_all(self)
