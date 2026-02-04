"""Query helpers for tape entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .entries import TapeEntry
from .store import TapeStore


@dataclass(frozen=True)
class TapeQuery:
    tape: str
    store: TapeStore
    _after_anchor: str | None = None
    _between: tuple[str, str] | None = None
    _kinds: tuple[str, ...] = field(default_factory=tuple)
    _limit: int | None = None

    def after_anchor(self, name: str | None = None) -> TapeQuery:
        anchor = name or "__last__"
        return TapeQuery(
            tape=self.tape,
            store=self.store,
            _after_anchor=anchor,
            _between=self._between,
            _kinds=self._kinds,
            _limit=self._limit,
        )

    def between_anchors(self, start: str, end: str) -> TapeQuery:
        return TapeQuery(
            tape=self.tape,
            store=self.store,
            _after_anchor=self._after_anchor,
            _between=(start, end),
            _kinds=self._kinds,
            _limit=self._limit,
        )

    def kinds(self, *kinds: str) -> TapeQuery:
        return TapeQuery(
            tape=self.tape,
            store=self.store,
            _after_anchor=self._after_anchor,
            _between=self._between,
            _kinds=tuple(kinds),
            _limit=self._limit,
        )

    def limit(self, value: int) -> TapeQuery:
        return TapeQuery(
            tape=self.tape,
            store=self.store,
            _after_anchor=self._after_anchor,
            _between=self._between,
            _kinds=self._kinds,
            _limit=value,
        )

    def all(self) -> list[TapeEntry]:
        entries = list(self._read_entries())
        if self._limit is not None:
            return entries[: self._limit]
        return entries

    def _read_entries(self) -> Iterable[TapeEntry]:
        entries = self.store.read(self.tape) or []
        start_index = 0
        end_index: int | None = None

        if self._between is not None:
            start_name, end_name = self._between
            start_index = _anchor_index(entries, start_name, default=0, forward=True)
            end_index = _anchor_index(entries, end_name, default=len(entries), forward=False)
            start_index = min(start_index + 1, len(entries))
            end_index = max(start_index, end_index)
        elif self._after_anchor is not None:
            anchor_name = self._after_anchor
            if anchor_name == "__last__":
                anchor_name = None
            anchor_index = _anchor_index(entries, anchor_name, default=-1, forward=False)
            start_index = min(anchor_index + 1, len(entries))

        sliced = entries[start_index:end_index]
        if self._kinds:
            return [entry for entry in sliced if entry.kind in self._kinds]
        return sliced


def _anchor_index(entries: Sequence[TapeEntry], name: str | None, *, default: int, forward: bool) -> int:
    if forward:
        rng = range(len(entries))
    else:
        rng = range(len(entries) - 1, -1, -1)
    for idx in rng:
        entry = entries[idx]
        if entry.kind != "anchor":
            continue
        if name and entry.payload.get("name") != name:
            continue
        return idx
    return default
