"""Query helpers for tape entries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace

from republic.tape.entries import TapeEntry
from republic.tape.store import TapeStore


@dataclass(frozen=True)
class TapeQuery:
    tape: str
    store: TapeStore
    _after_anchor: str | None = None
    _after_last: bool = False
    _between: tuple[str, str] | None = None
    _kinds: tuple[str, ...] = field(default_factory=tuple)
    _limit: int | None = None

    def after_anchor(self, name: str) -> TapeQuery:
        if not name:
            return replace(self, _after_anchor=None, _after_last=False)
        return replace(self, _after_anchor=name, _after_last=False)

    def last_anchor(self) -> TapeQuery:
        return replace(self, _after_anchor=None, _after_last=True)

    def between_anchors(self, start: str, end: str) -> TapeQuery:
        return replace(self, _between=(start, end))

    def kinds(self, *kinds: str) -> TapeQuery:
        return replace(self, _kinds=kinds)

    def limit(self, value: int) -> TapeQuery:
        return replace(self, _limit=value)

    def all(self) -> Iterable[TapeEntry]:
        return self.store.fetch_all(self)
